import json
import signal
from typing import TypedDict, Optional
from contextlib import contextmanager
import modal
import os
import requests
import datetime
import shutil
import time
import tempfile
import re
import sentry_sdk
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from db import Database
from openai import OpenAI
from github import Github
from eth_account import Account
from eth_account.messages import encode_defunct
import git
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from neynar import get_user_casts, format_cast
from notifications import send_notification
from modal.container_process import ContainerProcess


import modal
from backend.config.project_config import ProjectConfig
from backend.utils.sandbox import SandboxCommandExecutor
from backend.services.vercel_service import VercelService
from backend.services.git_service import GitService


MODAL_APP_NAME = ProjectConfig.APP_NAME
UPDATE_SNAPSHOT_INTERVAL_DAYS = 1

# Default Project Files to Modify
DEFAULT_PROJECT_FILES = [
    "src/components/Frame.tsx",
    "src/lib/constants.ts"
]

# Additional Constants
DOMAIN_ASSOCIATION_PATH = "src/app/.well-known/farcaster.json/route.ts"
VERCEL_FRAMEWORK = ProjectConfig.VERCEL["FRAMEWORK"]
VERCEL_INSTALL_COMMAND = ProjectConfig.VERCEL["INSTALL_CMD"]
VERCEL_BUILD_COMMAND = ProjectConfig.VERCEL["BUILD_CMD"]
VERCEL_OUTPUT_DIR = ProjectConfig.VERCEL["OUTPUT_DIR"]

DEFAULT_NOTIFICATION_TITLE = "Your {project_name} frame is building"
DEFAULT_NOTIFICATION_BODY = "Frameception has prepared your frame, it's almost ready! 🚀"


def setup_sentry():
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={"continuous_profiling_auto_start": True},
    )


# Create or reference volumes
github_repos = modal.Volume.from_name(
    ProjectConfig.VOLUMES["GITHUB_REPOS"], create_if_missing=True)
shared_node_modules = modal.Volume.from_name(
    ProjectConfig.VOLUMES["SHARED_NODE_MODULES"],
    create_if_missing=True
)
pnpm_store = modal.Volume.from_name(
    ProjectConfig.VOLUMES["PNPM_STORE"],
    create_if_missing=True
)
volumes = {
    ProjectConfig.PATHS["GITHUB_REPOS"]: github_repos,
    "/shared/node_modules": shared_node_modules,
    "/pnpm-store": pnpm_store
}

base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .env(ProjectConfig.CONTAINER_ENV_VARS)
    # Add build tools
    .apt_install("git", "curl", "python3-dev", "build-essential")
    .pip_install(
        "fastapi[standard]",
        "aider-chat[playwright]",
        "aider-install",
        "GitPython",
        "PyGithub",
        "requests",
        "openai",
        "supabase",
        "eth-account",
        "sentry-sdk[fastapi]",
        "redis",
    )
    .run_commands(
        "playwright install --with-deps chromium",
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        "curl -fsSL https://get.pnpm.io/install.sh | SHELL=/bin/bash bash -",  # Set SHELL here
        "pnpm add -g node-gyp",
        "aider-install",
    )
    .run_function(setup_sentry, secrets=[modal.Secret.from_name("sentry-secret")])
)

app = modal.App(name=MODAL_APP_NAME, image=base_image)


def verify_github_setup(gh: Github, job_id: str, db: Database) -> None:
    """Verify GitHub setup and permissions."""
    try:
        org = gh.get_organization(ProjectConfig.GITHUB["ORG_NAME"])
        if not org:
            raise Exception(f"Could not access organization: {
                            ProjectConfig.GITHUB['ORG_NAME']}")
        db.add_log(job_id, "github", "GitHub organization access verified")
    except Exception as e:
        raise Exception(f"GitHub organization access failed: {str(e)}")


def generate_project_name(prompt: str, llm_client: OpenAI) -> str:
    """Generate a project name from the user's prompt using LLM."""
    try:
        response = llm_client.chat.completions.create(
            model="deepseek-coder",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant that generates short, memorable project names for a Farcaster Frame project. Only respond with the project name, 2-3 words max, no 'or' or &*/ chars."
            }, {
                "role": "user",
                "content": f"Generate a short, memorable project name based on this description: {prompt}"
            }],
            max_tokens=50
        )
        project_name = response.choices[0].message.content.strip().replace(
            '"', '')
        return project_name[:50]  # Limit length
    except Exception as e:
        print(f"Warning: Could not generate project name: {str(e)}")
        return "new-frame-project"


def get_unique_repo_name(gh: Github, base_name: str, max_attempts: int = 100) -> str:
    """Get a unique repository name by appending numbers if needed."""
    org = gh.get_organization(ProjectConfig.GITHUB["ORG_NAME"])
    name = base_name
    attempt = 1

    while attempt < max_attempts:
        try:
            org.get_repo(name)
            name = f"{base_name}-{attempt}"
            attempt += 1
        except Exception as e:
            if "Not Found" in str(e):
                return name
            raise
    raise Exception(f"Could not find unique name after {
                    max_attempts} attempts")


def get_shortest_vercel_domain(project_name: str) -> str:
    """Get the shortest Vercel domain for a project."""
    return f"{project_name}.vercel.app"


def get_project_setup_prompt(project_name: str, user_prompt: str, user_context: Dict[str, Any]) -> str:
    """Generate the initial setup prompt for the project."""
    return f"""Create a Farcaster Frame called "{project_name}" based on this description:
{user_prompt}

Focus on:
1. Updating the Frame component in src/components/Frame.tsx
2. Adding any needed constants to src/lib/constants.ts
3. Keeping the implementation simple and focused
4. Using best practices for Frames

The frame should be engaging and interactive while following Farcaster Frame best practices."""


def improve_user_instructions(prompt: str, llm_client: OpenAI) -> str:
    """Use LLM to improve and expand the user's instructions."""
    try:
        response = llm_client.chat.completions.create(
            model="deepseek-coder",
            messages=[{
                "role": "system",
                "content": "You are an expert at improving and clarifying instructions for creating Farcaster Frames."
            }, {
                "role": "user",
                "content": f"Improve these instructions for creating a Farcaster Frame, adding specific technical details while keeping the original intent:\n\n{prompt}"
            }],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Warning: Could not improve instructions: {str(e)}")
        return prompt


def generate_domain_association(domain: str) -> Dict[str, Any]:
    """Generate Farcaster domain association data."""
    # Create a new Ethereum account for signing
    account = Account.create()

    # Prepare the message
    message = {
        "domain": domain,
        "timestamp": int(time.time()),
        "expirationTime": int(time.time()) + (90 * 24 * 60 * 60)  # 90 days
    }

    # Sign the message
    encoded_message = encode_defunct(
        text=json.dumps(message, separators=(',', ':')))
    signature = account.sign_message(encoded_message)

    return {
        "message": message,
        "signature": signature.signature.hex(),
        "signingKey": account.key.hex(),
        "json": {
            "message": message,
            "signature": signature.signature.hex(),
            "signingKey": account.key.hex()
        }
    }

###############################################################################
# Utility Functions
###############################################################################


class UserContext(TypedDict):
    fid: int
    username: Optional[str]
    displayName: Optional[str]
    pfpUrl: Optional[str]
    location: Optional[dict]


def expand_user_prompt_with_farcaster_context(prompt: str, user_context: UserContext):
    try:
        last_ten_casts = get_user_casts(user_context["fid"], 10)
        formatted_casts = [format_cast(c) for c in last_ten_casts]
        cast_context = "\n".join([c for c in formatted_casts if c])
        return f"{prompt}\nBelow are recent Farcaster posts from {user_context.get('username', '')} {user_context.get('displayName', '')}:\n{cast_context}"
    except Exception as e:
        print(
            f"Warning: expand_user_prompt_with_farcaster_context error: {str(e)}")
        return prompt


def sanitize_project_name(name: str) -> str:
    import re
    sanitized = re.sub(r"[^a-z0-9._-]", "-", name.lower())
    sanitized = re.sub(r"-+", "-", sanitized)
    return sanitized[:100].strip("-") or "new-frame-project"

###############################################################################
# update_code_webhook -> triggers update_code()
###############################################################################


@app.function()
@modal.web_endpoint(label="update-code", method="POST", docs=True)
def update_code_webhook(data: dict) -> str:
    """
    Webhook endpoint to trigger code update for a repository.
    """
    if not data.get("project_id") or not data.get("prompt"):
        return "Please provide project_id and prompt", 400

    print(f"[update_code_webhook] Received data: {data}")

    # Create an async function call without waiting for results
    function_call = update_code.spawn(data)

    # You could optionally store the function_call.object_id somewhere
    # to check status later

    return "Update code initiated"

###############################################################################
# update_code => clones or updates local repo, builds snapshot, runs build or Aider
###############################################################################


@contextmanager
def sigint_handler(job_id: str, db: Database):
    """Context manager for handling SIGINT with job cleanup"""
    def handle_sigint(signum, frame):
        print(f"\n[SIGINT] Received interrupt signal, marking job {
              job_id} as failed...")
        try:
            db.update_job_status(
                job_id,
                "failed",
                "Job interrupted by system or user"
            )
            db.add_log(job_id, "backend", "Job interrupted by SIGINT")
        except Exception as e:
            print(f"[SIGINT] Error updating job status: {e}")

    # Set up signal handler
    original_handler = signal.signal(signal.SIGINT, handle_sigint)
    try:
        yield
    except KeyboardInterrupt:
        handle_sigint(None, None)
    finally:
        # Restore original handler
        signal.signal(signal.SIGINT, original_handler)


@app.function(
    volumes=volumes,
    timeout=ProjectConfig.TIMEOUTS["PROJECT_SETUP"],
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret"),
        modal.Secret.from_name("neynar-secret"),
        modal.Secret.from_name("redis-secret"),
    ],
)
def update_code(data: dict) -> str:
    from db import Database
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput

    prompt = data.get("prompt", "")
    project_id = data.get("project_id", "")
    user_context = data.get("user_context", {})
    db = Database()

    project = db.get_project(project_id)
    if not project:
        return f"Project {project_id} not found", 404

    job_id = db.create_job(project_id, job_type="update_code", data=data)

    with sigint_handler(job_id, db):
        try:
            repo_path = project["repo_url"].replace("https://github.com/", "")
            git_service = GitService(repo_path, job_id, db)

            # Ensure repo is ready and up-to-date
            repo = git_service.ensure_repo_ready()
            print('done ensure_repo_ready', repo)
            if not git_service.safe_pull():
                raise Exception("Failed to sync with remote repository")

            repo_dir = git_service.repo_dir  # Get repo_dir from GitService

            # Verify working directory before creating sandbox
            print(f'Verifying repo directory: {repo_dir}')
            if not os.path.exists(repo_dir):
                raise Exception(f"Repository directory not found: {repo_dir}")
            if not os.path.exists(os.path.join(repo_dir, "package.json")):
                raise Exception(f"package.json not found in {repo_dir}")

            print('Creating Modal sandbox...')
            # Create sandbox with explicit volume mounting
            sandbox = modal.Sandbox.create(
                image=base_image,
                workdir=repo_dir,
                cpu=2.0,
                memory=4096,
                timeout=ProjectConfig.TIMEOUTS["CODE_UPDATE"],
                volumes=volumes,
            )

            # Verify sandbox working directory
            verify_cmd = sandbox.exec("ls", "-la", workdir=repo_dir)
            for line in verify_cmd.stdout:
                print(f"[SANDBOX_VERIFY] {line.strip()}")
            verify_cmd.wait()

            print("[update_code] Running pnpm install with shared node_modules...")
            install_proc = sandbox.exec(
                "pnpm",
                "install",
                # "--frozen-lockfile", # bring this back in a bit
                workdir=repo_dir
            )

            for line in install_proc.stdout:
                line_str = line.strip()
                print(f"[INSTALL STDOUT] {line_str}")

            for line in install_proc.stderr:
                line_str = line.strip()
                print(f"[INSTALL STDERR] {line_str}")

            install_proc.wait()

            # Create the test command object
            sandbox_test_cmd = SandboxCommandExecutor(
                sandbox, job_id, db, repo_dir)

            # 5) Use Aider for code modifications
            expansions = ["farcaster", " me ", " my ", " mine ",
                          " i ", " we ", " our ", "@", "cast", "profile"]
            if any(word in prompt.lower() for word in expansions):
                prompt = expand_user_prompt_with_farcaster_context(
                    prompt, user_context)
                print(f"[update_code] Expanded prompt with Farcaster context.")

            os.chdir(repo_dir)
            fnames = [os.path.join(repo_dir, f) for f in DEFAULT_PROJECT_FILES]
            llm_docs_dir = f"{repo.working_tree_dir}/llm_docs"
            read_only_fnames = []
            if os.path.exists(llm_docs_dir):
                read_only_fnames = [
                    os.path.join(llm_docs_dir, f)
                    for f in os.listdir(llm_docs_dir)
                    if os.path.isfile(os.path.join(llm_docs_dir, f))
                ]

            io = InputOutput(yes=True, root=repo_dir)
            model = Model(
                model="deepseek/deepseek-coder",
                weak_model=None,
                editor_model="deepseek/deepseek-coder"
            )
            coder = Coder.create(
                io=io,
                fnames=fnames,
                auto_test=True,
                main_model=model,
                test_cmd=sandbox_test_cmd,
                read_only_fnames=read_only_fnames
            )

            print(f"[update_code] Running Aider with prompt: {prompt}")
            try:
                aider_result = coder.run(prompt)
                print(f"[update_code] Aider result (truncated): {
                    aider_result[:250]}")

                # Handle any pnpm commands in the Aider output
                _handle_pnpm_commands(
                    aider_result, sandbox, git_service, job_id, db)

            except Exception as e:
                error_msg = f"Aider run failed: {str(e)}"
                print(f"[update_code] {error_msg}")
                db.add_log(job_id, "backend", error_msg)
                db.update_job_status(job_id, "failed", error_msg)
                sandbox.terminate()
                return error_msg

            # Push changes if any
            if not git_service.safe_push("Automated update from Aider"):
                db.add_log(job_id, "git",
                           "Warning: Failed to push changes to remote")

            # 7) Update job status
            db.update_job_status(job_id, "completed")
            print("[update_code] Finished code update successfully.")
            sandbox.terminate()
            return f"Successfully updated code for {repo_path} in project {project_id}"
        except Exception as e:
            error_msg = f"Error updating code: {str(e)}"
            print(f"[update_code] {error_msg}")
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", error_msg)
            raise  # Re-raise to trigger Modal's retry mechanism if needed

###############################################################################
# Example create_frame_project_webhook -> triggers setup_frame_project
###############################################################################


@app.function(
    secrets=[modal.Secret.from_name("supabase-secret")]
)
@modal.web_endpoint(label="create-frame-project-webhook", method="POST", docs=True)
def create_frame_project_webhook(data: dict) -> dict:
    """
    Webhook that creates a project record and triggers background job.
    """
    import uuid
    from db import Database
    db = Database()

    required_fields = ["prompt", "description", "userContext"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    fid = int(data["userContext"]["fid"])
    project_id = db.create_project(fid_owner=fid, repo_url="", frontend_url="")
    job_id = db.create_job(project_id, job_type="setup_project", data=data)
    db.add_log(job_id, "backend", "Frame initiated")

    setup_frame_project.spawn(data, project_id, job_id)
    return {
        "status": "pending",
        "projectId": project_id,
        "jobId": job_id,
        "message": "Project creation started"
    }

###############################################################################
# Additional Setup Logic
###############################################################################


def _handle_pnpm_commands(aider_result: str, sandbox: modal.Sandbox, git_service: GitService, job_id: str, db: Database) -> None:
    """Parse and execute pnpm commands from Aider output"""
    import re

    # Updated pattern to explicitly handle newlines after bash
    pattern = r"```bash[\s\n]*pnpm add (.*?)```"
    matches = re.finditer(pattern, aider_result, re.DOTALL)

    # Rest of the function remains the same
    for match in matches:
        packages = match.group(1).strip()
        if not packages:
            continue

        try:
            print(f"[update_code] Installing packages: {packages}")
            db.add_log(job_id, "backend", f"Installing packages: {packages}")

            # Run pnpm add command
            install_proc = sandbox.exec(
                "pnpm",
                "add",
                *packages.split(),
                workdir=git_service.repo_dir
            )

            # Capture and log output
            for line in install_proc.stdout:
                line_str = line.strip()
                print(f"[PNPM STDOUT] {line_str}")

            for line in install_proc.stderr:
                line_str = line.strip()
                print(f"[PNPM STDERR] {line_str}")

            exit_code = install_proc.wait()
            if exit_code != 0:
                raise Exception(
                    f"pnpm add command failed with exit code {exit_code}")

            # Commit and push changes
            if git_service.safe_push("Added new dependencies via pnpm"):
                print("Successfully committed and pushed new dependencies")
            else:
                print("Warning: Failed to push dependency changes")

        except Exception as e:
            error_msg = f"Error installing packages: {str(e)}"
            print(f"[update_code] {error_msg}")


def cleanup_project_repo(repo_path: str) -> None:
    import shutil
    full_path = f"/github-repos/{repo_path}"
    if os.path.exists(full_path):
        print(f"[cleanup_project_repo] removing {full_path}")
        shutil.rmtree(full_path)
    else:
        print(f"[cleanup_project_repo] {full_path} not found")


class SetupError:
    """Handles setup errors with consistent logging and cleanup."""

    def __init__(self, db: Database, job_id: str):
        self.db = db
        self.job_id = job_id

    def handle(self, error: Exception, stage: str, cleanup_repo: str = None):
        """Handle setup error with logging and optional cleanup."""
        error_msg = f"Error in {stage}: {str(error)}"
        print(f"[setup_frame_project] {error_msg}")
        self.db.add_log(self.job_id, "backend", error_msg)
        self.db.update_job_status(self.job_id, "failed", error_msg)

        if cleanup_repo:
            self._cleanup_repo(cleanup_repo)

    def _cleanup_repo(self, repo_path: str):
        """Clean up repository directory after error."""
        try:
            cleanup_project_repo(repo_path)
        except Exception as e:
            print(f"Warning: cleanup failed: {str(e)}")


class ProjectSetupValidator:
    """Validates project setup input data."""

    @staticmethod
    def validate_user_context(user_context: dict) -> None:
        """Validate required user context fields."""
        if not user_context:
            raise ValueError("Missing userContext in request data")

        if not user_context.get("username"):
            raise ValueError("Missing username in userContext")

        if not user_context.get("fid"):
            raise ValueError("Missing fid in userContext")

    @staticmethod
    def validate_project_data(data: dict) -> None:
        """Validate required project data fields."""
        required_fields = ["prompt", "description", "userContext"]
        missing_fields = [
            field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {
                             ', '.join(missing_fields)}")


@app.function(
    retries=1,
    volumes=volumes,
    timeout=ProjectConfig.TIMEOUTS["PROJECT_SETUP"],
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret"),
        modal.Secret.from_name("neynar-secret"),
        modal.Secret.from_name("redis-secret"),
    ],
)
def setup_github_repo(gh: Github, repo_name: str, description: str, job_id: str, db: Database) -> object:
    """Create and set up a new GitHub repository."""
    import shutil
    import git

    db.add_log(job_id, "github",
               f"Attempting to create repo '{repo_name}'")
    org = gh.get_organization(ProjectConfig.GITHUB["ORG_NAME"])
    try:
        existing_repo = org.get_repo(repo_name)
        if existing_repo:
            raise Exception(f"Repository '{repo_name}' already exists")
    except Exception as e:
        if "Not Found" not in str(e):
            raise

    repo = org.create_repo(
        name=repo_name, description=description, private=False)
    db.add_log(job_id, "github", f"Created repository: {repo.html_url}")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            template_path = os.path.join(temp_dir, "template")
            git.Repo.clone_from(
                ProjectConfig.GITHUB["TEMPLATE_REPO"], template_path)
            db.add_log(job_id, "github", "Cloned template repo")

            new_repo_url = f"https://{os.environ['GITHUB_TOKEN']
                                      }@github.com/{repo.full_name}.git"
            new_repo_path = os.path.join(temp_dir, "new-repo")
            new_repo = git.Repo.clone_from(new_repo_url, new_repo_path)
            db.add_log(job_id, "github", "Cloned new repository (empty)")

            new_repo.config_writer().set_value(
                "user", "name", ProjectConfig.GITHUB["COMMIT_NAME"]).release()
            new_repo.config_writer().set_value(
                "user", "email", ProjectConfig.GITHUB["COMMIT_EMAIL"]).release()

            for item in os.listdir(template_path):
                if item != ".git":
                    src = os.path.join(template_path, item)
                    dst = os.path.join(new_repo_path, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

            new_repo.git.add(A=True)
            new_repo.index.commit("Initial bulk copy from template")
            new_repo.git.push("origin", "main")
            db.add_log(job_id, "github", "Successfully copied template files")
            return repo
        except Exception as e2:
            raise Exception(f"Failed during repository setup: {str(e2)}")


def get_vercel_config() -> dict:
    """Get Vercel configuration with required environment variables."""
    required_vars = ["VERCEL_TEAM_ID", "VERCEL_TOKEN"]
    for var in required_vars:
        if var not in os.environ:
            raise EnvironmentError(
                f"Missing required environment variable: {var}")

    return {
        "TEAM_ID": os.environ["VERCEL_TEAM_ID"],
        "TOKEN": os.environ["VERCEL_TOKEN"],
        "FRAMEWORK": VERCEL_FRAMEWORK,
        "INSTALL_CMD": VERCEL_INSTALL_COMMAND,
        "BUILD_CMD": VERCEL_BUILD_COMMAND,
        "OUTPUT_DIR": VERCEL_OUTPUT_DIR
    }


class ProjectSetup:
    """Manages the frame project setup process."""

    def __init__(self, data: dict, project_id: str, job_id: str):
        self.data = data
        self.project_id = project_id
        self.job_id = job_id
        self.db = Database()
        self.error_handler = SetupError(self.db, self.job_id)

    def run(self) -> None:
        """Execute the full setup process."""
        try:
            self._validate_and_init()
            repo = self._setup_github()
            vercel_info = self._setup_vercel(repo)
            self._update_project_info(repo, vercel_info)
            self._run_code_updates(repo)
            self._send_notification()
            self._cleanup(repo)
        except Exception as e:
            self.error_handler.handle(e, "project setup",
                                      cleanup_repo=getattr(self, 'repo', None))
            return

    def _validate_and_init(self) -> None:
        """Validate input and initialize services."""
        ProjectSetupValidator.validate_project_data(self.data)
        ProjectSetupValidator.validate_user_context(self.data["userContext"])

        self.gh = Github(os.environ["GITHUB_TOKEN"])
        verify_github_setup(self.gh, self.job_id, self.db)

        self.deepseek = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )

        self.user_context = self.data["userContext"]
        self.project_name = generate_project_name(
            self.data["prompt"], self.deepseek)

    def _setup_github(self) -> object:
        """Set up GitHub repository."""
        base_repo_name = f"{
            self.user_context['username']}-{sanitize_project_name(self.project_name)}"
        repo_name = get_unique_repo_name(self.gh, base_repo_name)

        self.db.add_log(self.job_id, "github",
                        f"Creating GitHub repository: {repo_name}")
        repo = setup_github_repo(
            self.gh, repo_name, self.data["description"], self.job_id, self.db)
        self.db.add_log(self.job_id, "github",
                        f"Created GitHub repo: {repo.html_url}")

        return repo

    def _setup_vercel(self, repo: object) -> dict:
        """Set up Vercel project and deployment."""
        vercel_config = get_vercel_config()
        vercel_service = VercelService(vercel_config, self.db, self.job_id)

        self.db.add_log(self.job_id, "vercel", "Creating Vercel project")
        vercel_project = vercel_service.create_project(repo.name, repo)

        return vercel_project

    def _update_project_info(self, repo: object, vercel_info: dict) -> None:
        """Update project information in database."""
        frontend_url = f"https://{get_shortest_vercel_domain(repo.name)}"
        self.db.client.table("projects").update({
            "name": self.project_name,
            "repo_url": repo.html_url,
            "frontend_url": frontend_url
        }).eq("id", self.project_id).execute()

        self.db.add_log(self.job_id, "vercel",
                        f"Deployment created at: {frontend_url}")

    def _run_code_updates(self, repo: object) -> None:
        """Run initial code updates and configurations."""
        setup_prompt = get_project_setup_prompt(
            self.project_name, self.data["prompt"], self.user_context)
        improved_prompt = improve_user_instructions(
            setup_prompt, self.deepseek)

        update_code.remote({
            "project_id": self.project_id,
            "repo_path": repo.full_name,
            "prompt": improved_prompt,
            "user_context": self.user_context,
            "job_type": "update_code_for_setup",
        })

        self._update_metadata(repo)
        self._setup_domain_association(repo)

    def _update_metadata(self, repo: object) -> None:
        """Update project metadata."""
        metadata_prompt = f"""
            Update the following files to customize the project metadata:
            1. In src/lib/constants.ts:
               set PROJECT_ID to "{self.project_name}"
               set PROJECT_TITLE to "{self.project_name}"
               set PROJECT_DESCRIPTION to a brief description of the project
            2. In src/app/opengraph-image.tsx:
               - Reflect the project name "{self.project_name}"
               - Include a matching color or layout
               - Keep a simple one-page brand layout
        """

        update_code.remote({
            "project_id": self.project_id,
            "repo_path": repo.full_name,
            "prompt": metadata_prompt,
            "job_type": "update_code_for_metadata",
        })

    def _setup_domain_association(self, repo: object) -> None:
        """Set up Farcaster domain association."""
        frontend_url = f"https://{get_shortest_vercel_domain(repo.name)}"
        domain = frontend_url[8:] if frontend_url.startswith(
            "https://") else frontend_url

        domain_assoc = generate_domain_association(domain)
        update_prompt = f"""
        Update src/app/.well-known/farcaster.json/route.ts so that the 'accountAssociation' field
        returns the following domain association:
        {json.dumps(domain_assoc['json'], indent=2)}
        Only update the accountAssociation field.
        """

        update_code.remote({
            "project_id": self.project_id,
            "repo_path": repo.full_name,
            "prompt": update_prompt,
            "job_type": "update_code_for_domain_association",
        })

    def _send_notification(self) -> None:
        """Send completion notification to user."""
        if "fid" in self.user_context:
            try:
                result = send_notification(
                    fid=self.user_context["fid"],
                    title=DEFAULT_NOTIFICATION_TITLE.format(
                        project_name=self.project_name),
                    body=DEFAULT_NOTIFICATION_BODY,
                )
                if result["state"] == "success":
                    self.db.add_log(
                        self.job_id,
                        "backend",
                        f"Sent completion notification to FID {
                            self.user_context['fid']}"
                    )
            except Exception as e:
                print("Warning: Could not send notification:", e)

    def _cleanup(self, repo: object) -> None:
        """Clean up temporary files."""
        try:
            cleanup_project_repo(repo.full_name)
        except Exception as e:
            print(f"Warning: cleanup failed: {str(e)}")


def create_vercel_deployment(repo_name: str, repo: object, headers: dict, vercel_config: dict) -> dict:
    """Create a deployment for the Vercel project."""
    deployment = requests.post(
        f"https://api.vercel.com/v13/deployments?teamId={
            vercel_config['TEAM_ID']}",
        headers=headers,
        json={"name": repo_name, "gitSource": {
            "type": "github", "repoId": str(repo.id), "ref": "main"}},
    ).json()

    if "error" in deployment:
        raise Exception(f"Failed to create deployment: {deployment['error']}")

    return deployment


def setup_frame_project(data: dict, project_id: str, job_id: str) -> None:
    """Full project creation job using state machine."""
    from backend.services.project_setup_service import ProjectSetupService, SetupState
    db = Database()

    with sigint_handler(job_id, db):
        setup_service = ProjectSetupService(data, project_id, job_id)
        while setup_service.state not in [SetupState.COMPLETE, SetupState.FAILED]:
            setup_service.advance()


###############################################################################
# Testing notifications
###############################################################################


@app.function()
@modal.web_endpoint(label="send-test-notification", method="POST", docs=True)
def send_test_notification(data: dict) -> dict:
    """
    Temporary webhook to test sending notifications to a user's FID.
    """
    if "fid" not in data:
        return {"error": "Missing required field: fid"}, 400

    fid = int(data["fid"])
    title = data.get("title", "Test Notification")
    body = data.get("body", "This is a test notification from Frameception")

    result = send_notification(fid=fid, title=title, body=body)
    print("[send-test-notification]", result)
    return {"status": "success", "result": result}
