import json
from backend import config
from backend.services.code_service import CodeService
from backend.types import UserContext
import modal

from backend.integrations.github_api import GithubApi
from backend.integrations.vercel_api import VercelApi
from backend.integrations.db import Database
from backend.integrations.deepseek import generate_project_name
from backend.utils.farcaster import generate_domain_association
from backend.utils.strings import sanitize_project_name


class ProjectService:
    def __init__(self, project_id: str, job_id: str, data: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.data = data
        self.user_context: UserContext = data["user_context"]

        self.db = Database()
        self.update_code_function = modal.Function.lookup(
            config.APP_NAME, config.MODAL_UPDATE_CODE_FUNCTION_NAME
        )

    def run(self):
        self._log("Starting project setup")

        self._validate_data()

        self._generate_project_name()

        # Core setup sequence
        self._setup_github_repo()
        self._setup_vercel_project()
        self._customize_template()

        self._log("Project setup completed")
        self.db.update_job_status(self.job_id, "completed")

    def _generate_project_name(self):
        project_name = generate_project_name(self.data["prompt"])
        self.project_name = sanitize_project_name(project_name)
        self._log(message=f"Generated project name: {self.project_name}")
        self.db.update_project(self.project_id, dict(name=project_name))

    def _setup_github_repo(self):
        self._log("Creating GitHub repository")
        github_api = GithubApi(
            self.job_id, self.project_name, username=self.user_context["username"]
        )
        self.repo_name = github_api.create_repo()
        github_api.copy_template_to_repo()
        self._log(f"GitHub repository setup complete {self.repo_name}")
        self.db.update_project(
            self.project_id, dict(repo_url=f"github.com/{self.repo_name}")
        )

    def _setup_vercel_project(self):
        self._log(message="Creating Vercel project")
        if not self.repo_name:
            raise Exception("Missing GitHub repository name to setup Vercel project")

        vercel_api = VercelApi(self.project_id, self.job_id)
        vercel_project_name = self.repo_name.split("/")[-1]
        vercel_api.create_project(
            project_name=vercel_project_name, repo_full_name=self.repo_name
        )
        self._log("Vercel project setup complete")

    def _customize_template(self):
        """Apply template customizations directly in volume"""
        print("customizing template")
        self.code_service = CodeService(self.project_id, self.job_id, self.user_context)
        customization_steps = [
            self._update_metadata,
            self._setup_domain_association,
            self._customize_from_user_input,
        ]

        for step in customization_steps:
            step()
        print("done customizing template")

    def _update_metadata(self):
        """Update metadata in code to reflect project setup"""
        self._log("Updating project metadata")
        metadata_prompt = get_metadata_prompt(self.project_name)
        self._call_update_code_function(metadata_prompt)

    def _setup_domain_association(self):
        """setup domain association for farcaster frame v2 to reflect user connection to new vercel domain"""
        self._log("Setting up domain association")
        print("should call update_code function via modal lookup here")
        domain = f"{self.project_name}.vercel.app"
        domain_association = generate_domain_association(domain)
        update_domain_association_prompt = f"""
        Update src/app/.well-known/farcaster.json/route.ts so that the 'accountAssociation' field returns the following domain association:
        {json.dumps(domain_association["json"], indent=2)}
        Only update the accountAssociation field.
        """
        self._call_update_code_function(update_domain_association_prompt)

    def _customize_from_user_input(self):
        """Apply user-specific customizations to frame configuration"""
        prompt = self.data["prompt"]
        self._log(f"Applying initial customization: {prompt[:50]}...")
        customize_from_user_input_prompt = get_template_customization_prompt(
            self.project_name, prompt
        )
        self._call_update_code_function(customize_from_user_input_prompt)

    def _call_update_code_function(self, prompt: str):
        print("calling update_code_function with prompt:", prompt)
        result = self.code_service.run(prompt=prompt)
        print("update_code_function result:", result)

    def _log(self, message: str, level: str = "info"):
        print(f"[{level.upper()}] ProjectService {message}")
        self.db.add_log(self.job_id, "setup", message)

    def _validate_data(self):
        if not self.data.get("prompt"):
            raise Exception("Missing user prompt in data")

        if not self.data.get("user_context"):
            raise Exception("Missing user context in data")

        user_context_keys = ["username", "fid"]
        for key in user_context_keys:
            if not self.data["user_context"].get(key):
                raise Exception(f"Missing {key} in user context")


def get_template_customization_prompt(project_name: str, user_prompt: str) -> str:
    """Generate initial setup prompt for project customization"""
    return f"""Create a Farcaster Frame called "{project_name}" based on:
{user_prompt}

Focus on:
1. Updating Frame component in src/components/Frame.tsx
2. Adding constants to src/lib/constants.ts
3. Simple implementation following Farcaster best practices"""


def get_metadata_prompt(project_name: str) -> str:
    """Generate metadata update prompt."""
    return f"""
Update the following files to customize the project metadata:
1. In src/lib/constants.ts:
   set PROJECT_ID to "{project_name}"
   set PROJECT_TITLE to "{project_name}"
   set PROJECT_DESCRIPTION to a brief description of the project
2. In src/app/opengraph-image.tsx:
   - Reflect the project name "{project_name}"
   - Include a matching color or layout
   - Keep a simple one-page brand layout
"""
