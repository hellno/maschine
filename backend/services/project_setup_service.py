from enum import Enum
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from modal import Function
from datetime import datetime
import json
import os
import requests
from github import Github
from modal import app

from backend.db import Database
from backend.services.git_service import GitService
from backend.services.vercel_service import VercelService
from backend.config.project_config import ProjectConfig
from backend.utils.helpers import generate_random_secret
from backend.utils.project_utils import (
    generate_project_name,
    get_project_setup_prompt,
    get_metadata_prompt,
    generate_domain_association,
    sanitize_project_name
)
from backend.notifications import send_notification


class SetupState(Enum):
    INIT = "init"
    VALIDATING = "validating"
    GITHUB_SETUP = "github_setup"
    VERCEL_SETUP = "vercel_setup"
    CODE_UPDATE = "code_update"
    METADATA_UPDATE = "metadata_update"
    DOMAIN_SETUP = "domain_setup"
    NOTIFICATION = "notification"
    COMPLETE = "complete"
    FAILED = "failed"


class SetupContext:
    """Holds all context data for the setup process"""

    def __init__(self, data: dict, project_id: str, job_id: str):
        self.data = data
        self.project_id = project_id
        self.job_id = job_id
        self.user_context = data.get("userContext", {})
        self.project_name: Optional[str] = None
        self.repo: Optional[object] = None
        self.vercel_info: Optional[dict] = None
        self.frontend_url: Optional[str] = None
        self.error: Optional[str] = None
        self.completed_steps: set = set()

    def to_dict(self) -> dict:
        """Convert context to serializable dict"""
        return {
            "data": self.data,
            "project_id": self.project_id,
            "job_id": self.job_id,
            "user_context": self.user_context,
            "project_name": self.project_name,
            "repo_full_name": self.repo.full_name if self.repo else None,
            "vercel_info": self.vercel_info,
            "frontend_url": self.frontend_url,
            "error": self.error,
            "completed_steps": list(self.completed_steps)
        }

    @classmethod
    def from_dict(cls, data: dict, project_id: str, job_id: str) -> 'SetupContext':
        """Create context from saved state"""
        context = cls(data.get("data", {}), project_id, job_id)
        context.user_context = data.get("user_context", {})
        context.project_name = data.get("project_name")
        context.vercel_info = data.get("vercel_info")
        context.frontend_url = data.get("frontend_url")
        context.error = data.get("error")
        context.completed_steps = set(data.get("completed_steps", []))

        # Reconnect to GitHub repo if it exists
        if data.get("repo_full_name"):
            gh = Github(os.environ["GITHUB_TOKEN"])
            try:
                org_name, repo_name = data["repo_full_name"].split("/")
                org = gh.get_organization(org_name)
                context.repo = org.get_repo(repo_name)
            except Exception as e:
                print(f"Warning: Could not reconnect to GitHub repo: {e}")

        return context


class ProjectSetupService:
    """Manages the frame project setup process with state transitions and recovery"""

    MAX_ATTEMPTS = 3  # Maximum number of setup attempts per state

    def __init__(self, data: dict, project_id: str, job_id: str):
        self.db = Database()
        # Initialize context directly instead of loading/creating
        self.context = SetupContext(data, project_id, job_id)
        # Start with INIT state
        self.state = SetupState.INIT
        # Get reference to update_code function
        self.update_code_fn = Function.from_name("frameception", "update_code")
        self.transitions = {
            SetupState.INIT: [SetupState.VALIDATING, SetupState.FAILED],
            SetupState.VALIDATING: [SetupState.GITHUB_SETUP, SetupState.FAILED],
            SetupState.GITHUB_SETUP: [SetupState.VERCEL_SETUP, SetupState.FAILED],
            SetupState.VERCEL_SETUP: [SetupState.CODE_UPDATE, SetupState.FAILED],
            SetupState.CODE_UPDATE: [SetupState.METADATA_UPDATE, SetupState.FAILED],
            SetupState.METADATA_UPDATE: [SetupState.DOMAIN_SETUP, SetupState.FAILED],
            SetupState.DOMAIN_SETUP: [SetupState.NOTIFICATION, SetupState.FAILED],
            SetupState.NOTIFICATION: [SetupState.COMPLETE, SetupState.FAILED],
            SetupState.COMPLETE: [],
            SetupState.FAILED: []
        }

    def advance(self) -> SetupState:
        """Advance to the next state based on current state"""
        try:
            self._log_state_transition()

            if self.state == SetupState.INIT:
                self._transition_to(SetupState.VALIDATING)
                self._validate_input()

            elif self.state == SetupState.VALIDATING:
                self._transition_to(SetupState.GITHUB_SETUP)
                self._setup_github()

            elif self.state == SetupState.GITHUB_SETUP:
                self._transition_to(SetupState.VERCEL_SETUP)
                self._setup_vercel()

            elif self.state == SetupState.VERCEL_SETUP:
                self._transition_to(SetupState.CODE_UPDATE)
                self._update_code()

            elif self.state == SetupState.CODE_UPDATE:
                self._transition_to(SetupState.METADATA_UPDATE)
                self._update_metadata()

            elif self.state == SetupState.METADATA_UPDATE:
                self._transition_to(SetupState.DOMAIN_SETUP)
                self._setup_domain()

            elif self.state == SetupState.DOMAIN_SETUP:
                self._transition_to(SetupState.NOTIFICATION)
                self._send_notification()

            elif self.state == SetupState.NOTIFICATION:
                self._transition_to(SetupState.COMPLETE)
                self._finalize_setup()

        except Exception as e:
            self.context.error = str(e)
            self._transition_to(SetupState.FAILED)
            self._handle_error(e)

        return self.state

    def _transition_to(self, new_state: SetupState) -> None:
        """Validate and perform state transition"""
        if new_state not in self.transitions[self.state]:
            raise ValueError(f"Invalid state transition from {
                             self.state} to {new_state}")

        self.state = new_state
        self._log_state_transition()
        self._update_job_status()

    def _validate_input(self) -> None:
        """Validate all required input data"""
        required_fields = ["prompt", "description", "userContext"]
        missing_fields = [
            f for f in required_fields if f not in self.context.data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {
                             ', '.join(missing_fields)}")

        if not self.context.user_context.get("fid"):
            raise ValueError("Missing fid in userContext")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _setup_github(self) -> None:
        """Set up GitHub repository"""
        from github import Github
        import tempfile
        import git
        import shutil

        gh = Github(os.environ["GITHUB_TOKEN"])

        try:
            # Generate project name
            self.context.project_name = self._generate_project_name()

            # Create repo with better error handling
            org = gh.get_organization(ProjectConfig.GITHUB["ORG_NAME"])
            self.context.repo = org.create_repo(
                name=self.context.project_name,
                description=self.context.data["description"],
                private=False
            )

            if not self.context.repo:
                raise Exception("Failed to create GitHub repository")

            self.db.add_log(
                self.context.job_id,
                "github",
                f"Created repo: {self.context.repo.full_name}"
            )

            # Set up repo with template files
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Clone template repo
                    template_path = os.path.join(temp_dir, "template")
                    self.db.add_log(self.context.job_id,
                                    "github", "Cloning template...")
                    git.Repo.clone_from(
                        ProjectConfig.GITHUB["TEMPLATE_REPO"],
                        template_path
                    )

                    # Clone new empty repo
                    new_repo_url = f"https://{os.environ['GITHUB_TOKEN']}@github.com/{
                        self.context.repo.full_name}.git"
                    new_repo_path = os.path.join(temp_dir, "new-repo")
                    self.db.add_log(self.context.job_id,
                                    "github", "Setting up new repo...")
                    new_repo = git.Repo.clone_from(new_repo_url, new_repo_path)

                    # Configure git user
                    new_repo.config_writer().set_value(
                        "user", "name", ProjectConfig.GITHUB["COMMIT_NAME"]
                    ).release()
                    new_repo.config_writer().set_value(
                        "user", "email", ProjectConfig.GITHUB["COMMIT_EMAIL"]
                    ).release()

                    # Copy template files to new repo
                    self.db.add_log(self.context.job_id, "github",
                                    "Copying template files...")
                    for item in os.listdir(template_path):
                        if item != ".git":
                            src = os.path.join(template_path, item)
                            dst = os.path.join(new_repo_path, item)
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)

                    # Commit and push template files
                    self.db.add_log(self.context.job_id, "github",
                                    "Pushing initial commit...")
                    new_repo.git.add(A=True)
                    new_repo.index.commit("Initial commit from template")
                    new_repo.git.push("origin", "main")

                except Exception as e:
                    self.db.add_log(
                        self.context.job_id,
                        "github",
                        f"Error in repo setup: {str(e)}"
                    )
                    raise

        except Exception as e:
            self.db.add_log(
                self.context.job_id,
                "github",
                f"Fatal error in GitHub setup: {str(e)}"
            )
            # Try to cleanup if repo was created
            if self.context.repo:
                try:
                    self.context.repo.delete()
                    self.db.add_log(self.context.job_id,
                                    "github", "Cleaned up failed repo")
                except:
                    pass
            raise

    def _setup_vercel(self) -> None:
        """Set up Vercel project and deployment"""
        vercel_config = {
            "TEAM_ID": os.environ["VERCEL_TEAM_ID"],
            "TOKEN": os.environ["VERCEL_TOKEN"],
            **ProjectConfig.VERCEL
        }

        vercel_service = VercelService(
            vercel_config, self.db, self.context.job_id)
        self.context.vercel_info = vercel_service.create_project(
            self.context.project_name,
            self.context.repo
        )

        self.context.frontend_url = f"https://{
            self.context.project_name}.vercel.app"

        # Update project record
        self.db.client.table("projects").update({
            "name": self.context.project_name,
            "repo_url": self.context.repo.html_url,
            "frontend_url": self.context.frontend_url,
            "vercel_project_id": self.context.vercel_info.get("id")
        }).eq("id", self.context.project_id).execute()

    def _update_code(self) -> None:
        """Update code with initial implementation"""
        setup_prompt = self._get_setup_prompt()

        # Use remote() instead of spawn() since we want to wait for completion
        self.update_code_fn.remote({
            "project_id": self.context.project_id,
            "repo_path": self.context.repo.full_name,
            "prompt": setup_prompt,
            "user_context": self.context.user_context,
            "job_type": "setup_project_initial"
        })

        self.db.add_log(
            self.context.job_id,
            "code",
            "Completed initial code update"
        )

    def _update_metadata(self) -> None:
        """Update project metadata"""
        metadata_prompt = self._get_metadata_prompt()

        self.update_code_fn.remote({
            "project_id": self.context.project_id,
            "repo_path": self.context.repo.full_name,
            "prompt": metadata_prompt,
            "job_type": "update_code_for_metadata"
        })

        self.db.add_log(
            self.context.job_id,
            "code",
            "Completed metadata update"
        )

    def _setup_domain(self) -> None:
        """Set up Farcaster domain association"""
        domain = self.context.frontend_url.replace("https://", "")
        domain_assoc = self._generate_domain_association(domain)

        update_prompt = f"""
        Update src/app/.well-known/farcaster.json/route.ts so that the 'accountAssociation' field
        returns the following domain association:
        {json.dumps(domain_assoc['json'], indent=2)}
        Only update the accountAssociation field.
        """

        self.update_code_fn.remote({
            "project_id": self.context.project_id,
            "repo_path": self.context.repo.full_name,
            "prompt": update_prompt,
            "job_type": "update_code_for_domain_association"
        })

        self.db.add_log(
            self.context.job_id,
            "domain",
            f"Set up domain association for {domain}"
        )

    def _send_notification(self) -> None:
        """Send completion notification"""
        from backend.notifications import send_notification

        if "fid" in self.context.user_context:
            try:
                send_notification(
                    fid=self.context.user_context["fid"],
                    title=f"Your {self.context.project_name} frame is ready!",
                    body="Frameception has prepared your frame, it's live! 🚀"
                )
            except Exception as e:
                self.db.add_log(
                    self.context.job_id,
                    "notification",
                    f"Warning: Could not send notification: {str(e)}"
                )

    def _finalize_setup(self) -> None:
        """Perform final cleanup and status updates"""
        self.db.update_job_status(self.context.job_id, "completed")

    def _handle_error(self, error: Exception) -> None:
        """Handle errors and update status"""
        error_msg = f"Error in {self.state.value}: {str(error)}"
        self.db.add_log(self.context.job_id, "backend", error_msg)
        self.db.update_job_status(self.context.job_id, "failed", error_msg)

    def _log_state_transition(self) -> None:
        """Log state transition"""
        self.db.add_log(
            self.context.job_id,
            "state",
            f"Project setup state: {self.state.value}"
        )

    def _update_job_status(self) -> None:
        """Update job status based on current state"""
        status = "completed" if self.state == SetupState.COMPLETE else "pending"
        self.db.update_job_status(self.context.job_id, status)

    def _generate_project_name(self) -> str:
        """Generate project name using LLM and prefix with username"""
        from openai import OpenAI

        deepseek = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )

        # Get username from user context
        username = self.context.user_context.get('username')
        if not username:
            # Fallback to fid if no username
            username = f"user{self.context.user_context.get('fid')}"
        
        # Generate base project name
        raw_name = generate_project_name(self.context.data['prompt'], deepseek)
        sanitized_base = sanitize_project_name(raw_name)
        
        # Combine username and project name
        sanitized_username = sanitize_project_name(username)
        full_name = f"{sanitized_username}-{sanitized_base}"
        
        print(f"Generated project name: {username} + {raw_name} -> {full_name}")
        
        return full_name

    def _get_setup_prompt(self) -> str:
        """Generate the initial setup prompt"""
        return get_project_setup_prompt(
            self.context.project_name,
            self.context.data['prompt']
        )

    def _get_metadata_prompt(self) -> str:
        """Generate metadata update prompt"""
        return get_metadata_prompt(self.context.project_name)

    def _generate_domain_association(self, domain: str) -> dict:
        """Generate Farcaster domain association"""
        return generate_domain_association(domain)
