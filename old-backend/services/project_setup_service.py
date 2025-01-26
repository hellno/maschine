import modal
import os
import shutil
import git
from backend.utils.github_utils import parse_github_url
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from backend.utils.project_utils import (
    sanitize_project_name,
    generate_domain_association,
)
from backend.integrations.db import Database
from backend.config.project_config import ProjectConfig
from backend.services.vercel_service import VercelService
from backend.services.project_volume import ProjectVolume
from backend.modal_instance import app


class ProjectSetup:
    def __init__(self, project_id: str, job_id: str, data: Dict[str, Any]):
        self.db = Database()
        self.project_id = project_id
        self.job_id = job_id
        self.data = data
        self.volume = ProjectVolume(project_id)
        self.repo = None

    @classmethod
    def from_user_input(cls, prompt: str, user_context: Dict[str, Any]):
        """Factory method for creating a new project setup from user input"""
        db = Database()

        # Create project first with empty URLs
        project_id = db.create_project(
            fid_owner=user_context["fid"],
            repo_url="",  # Will be updated during setup
            frontend_url="",  # Will be updated during setup
        )

        # Create initial job record
        job_data = {
            "prompt": prompt,
            "user_context": user_context,
            "project_name": user_context.get("project_name"),
        }
        job_id = db.create_job(
            project_id=project_id, job_type="setup_project", data=job_data
        )

        return cls(db, project_id, job_id, job_data)

    def run(self):
        """Atomic project setup sequence"""
        try:
            self._log("Starting project setup")

            # Core setup sequence
            self._setup_github_repository()
            self._setup_vercel_project()
            self._customize_template()
            self._finalize_project()

            self._log("Project setup completed")
            self.db.update_job_status(self.job_id, "completed")
        except Exception as e:
            self._handle_error(e)
            raise
        finally:
            self._clean_temporary_files()

    def _setup_github_repository(self):
        """Clone and initialize repository in S3 volume"""
        repo_path = self.volume.paths["repo"]

        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)

        self.repo = git.Repo.clone_from(
            ProjectConfig.GITHUB["TEMPLATE_REPO"], repo_path, depth=1
        )

        # Validate URL format using shared parser
        org, repo = parse_github_url(ProjectConfig.GITHUB["TEMPLATE_REPO"])
        self._log(f"Cloned repository: {org}/{repo}")

    def _setup_vercel_project(self):
        """Set up Vercel project using volume contents"""
        vercel_service = VercelService(
            config={
                "TEAM_ID": os.environ["VERCEL_TEAM_ID"],
                "TOKEN": os.environ["VERCEL_TOKEN"],
                **ProjectConfig.VERCEL,
            },
            db=self.db,
            repo=self.repo,
            job_id=self.job_id,
        )

        project_name = self.data.get("project_name", f"project-{self.project_id[:8]}")
        self.vercel_info = vercel_service.create_project(project_name)

        self.db.update_project(
            self.project_id, {"vercel_project_id": self.vercel_info["id"]}
        )

        # Update project URLs now that setup is complete
        self.db.update_project(
            self.project_id,
            {
                "repo_url": ProjectConfig.GITHUB["TEMPLATE_REPO"],
                "frontend_url": self.vercel_info.get("url", ""),
            },
        )

    def _customize_template(self):
        """Apply template customizations directly in volume"""
        customization_steps = [
            self._apply_initial_customization,
            self._update_metadata,
            self._setup_domain_association,
        ]

        for step in customization_steps:
            step()

    def _apply_initial_customization(self):
        """Apply user-specific customizations to frame configuration"""
        prompt = self.data["prompt"]
        self._log(f"Applying initial customization: {prompt[:50]}...")

        # Modify frame configuration file
        frame_config_path = os.path.join(
            self.volume.paths["repo"], "src/components/Frame.tsx"
        )
        if not os.path.exists(frame_config_path):
            raise Exception("Frame configuration file not found")

        try:
            with open(frame_config_path, "r+") as f:
                content = f.read()
                # Inject user prompt into frame config
                modified_content = content.replace(
                    "// USER_PROMPT_PLACEHOLDER", f"const userPrompt = `{prompt}`;"
                )
                f.seek(0)
                f.write(modified_content)
                f.truncate()

            self._log("Updated frame configuration with user prompt")

        except Exception as e:
            raise Exception(f"Failed to apply initial customization: {str(e)}")

    def _update_metadata(self):
        """Update project metadata in package.json"""
        self._log("Updating project metadata")

        package_path = os.path.join(self.volume.paths["repo"], "package.json")
        if not os.path.exists(package_path):
            raise Exception("package.json not found")

        try:
            with open(package_path, "r+") as f:
                pkg = json.load(f)

                # Update basic metadata
                pkg["name"] = sanitize_project_name(
                    self.data.get("project_name", f"project-{self.project_id[:8]}")
                )
                pkg["version"] = "1.0.0"
                pkg["description"] = self.data.get(
                    "description", "A custom Farcaster frame"
                )

                f.seek(0)
                json.dump(pkg, f, indent=2)
                f.truncate()

            self._log("Updated package.json metadata")

        except Exception as e:
            raise Exception(f"Failed to update metadata: {str(e)}")

    def _setup_domain_association(self):
        """Configure domain association file"""
        self._log("Setting up domain association")

        domain_path = os.path.join(
            self.volume.paths["repo"], "src/app/.well-known/farcaster.json/route.ts"
        )
        os.makedirs(os.path.dirname(domain_path), exist_ok=True)

        try:
            with open(domain_path, "w") as f:
                f.write(generate_domain_association(self.data))

            self._log("Created domain association file")

        except Exception as e:
            raise Exception(f"Failed to setup domain association: {str(e)}")

    def _finalize_project(self):
        """Final setup steps with validation"""
        self._log("Finalizing project setup")

        # Verify critical files
        required_files = [
            "package.json",
            "src/components/Frame.tsx",
            "src/app/.well-known/farcaster.json/route.ts",
        ]

        for rel_path in required_files:
            abs_path = os.path.join(self.volume.paths["repo"], rel_path)
            if not os.path.exists(abs_path):
                raise Exception(f"Missing critical file: {rel_path}")

        # Verify package.json structure
        package_path = os.path.join(self.volume.paths["repo"], "package.json")
        with open(package_path) as f:
            pkg = json.load(f)
            if "scripts" not in pkg or "build" not in pkg["scripts"]:
                raise Exception("Invalid package.json structure")

        self._log("Project validation passed")

    def _handle_error(self, error: Exception):
        """Error handling with rollback"""
        error_msg = f"Setup failed: {str(error)}"
        self._log(error_msg, level="error")
        self.db.update_job_status(self.job_id, "failed", error_msg)
        self.volume.delete()

    def _clean_temporary_files(self):
        """S3-specific cleanup using path removal"""
        for path in [self.volume.paths["tmp"], self.volume.paths["build"]]:
            if os.path.exists(path):
                shutil.rmtree(path)

    def _log(self, message: str, level: str = "info"):
        """Unified logging method"""
        print(f"[{level.upper()}] {message}")
        self.db.add_log(self.job_id, "setup", message)


@app.function(
    schedule=modal.Period(days=1),
    secrets=[
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("aws-secret"),
    ],
)
def cleanup_inactive_projects():
    """Daily cleanup of inactive project volumes"""
    db = Database()
    cutoff = datetime.now() - timedelta(days=7)

    inactive_projects = (
        db.client.table("projects")
        .select("id, last_accessed_at")
        .lt("last_accessed_at", cutoff.isoformat())
        .execute()
        .data
    )

    for project in inactive_projects:
        project_id = project["id"]
        volume = ProjectVolume(project_id)
        volume.delete()

        db.add_log(
            "system-cleanup",
            "volume",
            f"Deleted volume for inactive project {project_id}",
        )
        print(f"Cleaned up project {project_id}")
