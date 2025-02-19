from backend.services.code_service import CodeService
from backend.services.context_enhancer import CodeContextEnhancer
from backend.services.prompts import (
    BREAKDOWN_SPEC_INTO_PLAN_PROMPT,
    CREATE_SPEC_PROMPT,
    MAKE_TODO_LIST_PROMPT,
    TEMPLATE_CUSTOMIZATION_PROMPT,
)
from backend.types import UserContext

from backend.integrations.github_api import GithubApi
from backend.integrations.vercel_api import VercelApi
from backend.integrations.db import Database
from backend.integrations.llm import generate_project_name, get_venice_ai_client, send_prompt_to_reasoning_model
from backend.utils.strings import sanitize_project_name


class SetupProjectService:
    def __init__(self, project_id: str, job_id: str, data: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.data = data
        self.user_context: UserContext = data["user_context"]

        self.db = Database()

    def run(self):
        """Fast initial setup without final verification"""
        self._log("Starting accelerated core setup")
        self._validate_data()
        self._generate_project_name()
        self._setup_github_repo()
        self._setup_vercel_project()
        self._apply_initial_customization()
        self.db.update_project(
            self.project_id,
            {"status": "created", "repo_url": f"github.com/{self.repo_name}"},
        )
        self.db.update_job_status(self.job_id, "awaiting_deployment")
        self._log("Core infrastructure ready for deployment")

    def _apply_initial_customization(self):
        """Only apply user's initial prompt customization"""
        prompt = self.data["prompt"]
        context = CodeContextEnhancer().get_relevant_context(prompt)

        # ai! save spec, plan, todo into a markdown file in the repo_dir
        # commit and push the changes to the repo
        # then run code service on the todo list
        # we can run the prompt using send_prompt_to_reasoning_model

        spec = CREATE_SPEC_PROMPT.format(context=context, prompt=prompt)
        plan = BREAKDOWN_SPEC_INTO_PLAN_PROMPT.format(spec=spec)
        todo = MAKE_TODO_LIST_PROMPT.format(plan=plan)

        self._log(f"Applying initial customization: {prompt[:50]}...")
        customize_from_user_input_prompt = TEMPLATE_CUSTOMIZATION_PROMPT.format(
            self.project_name, prompt
        )

        self._log(
            f"Apply initial customization with prompt: {customize_from_user_input_prompt}"
        )
        code_service = CodeService(self.project_id, self.job_id, self.user_context)
        result = code_service.run(customize_from_user_input_prompt)
        self._log(f"Customization result: {result}")

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
