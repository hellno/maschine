import re

from backend.services.code_service import CodeService
from backend.services.context_enhancer import CodeContextEnhancer
from backend.services.prompts import (
    CREATE_PROMPT_PLAN_PROMPT,
    CREATE_SPEC_PROMPT,
    CREATE_TODO_LIST_PROMPT,
    IMPLEMENT_TODO_LIST_PROMPT,
    RETRY_IMPLEMENT_TODO_LIST_PROMPT,
)
from backend.types import UserContext
from backend.integrations.github_api import GithubApi
from backend.integrations.vercel_api import VercelApi
from backend.integrations.db import Database
from backend.integrations.llm import (
    generate_project_name,
    send_prompt_to_reasoning_model,
)
from backend.utils.strings import sanitize_project_name
from backend.config import SETUP_COMPLETE_COMMIT_MESSAGE


class SetupProjectService:
    def __init__(self, project_id: str, job_id: str, data: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.data = data
        self.user_context: UserContext = data["user_context"]
        self.db = Database()

    def run(self):
        """Fast initial setup without final verification"""
        try:
            self._log("Starting core setup")
            self._validate_data()
            self._generate_project_name()
            self._setup_github_repo()
            self._setup_vercel_project()
            self._apply_initial_customization()
            self.db.update_project(
                self.project_id,
                {
                    "status": "created",
                },
            )
            self.db.update_job_status(self.job_id, "completed")
            self._log("finished the project setup")
        except Exception as e:
            print(f"Failed to complete core setup. Error: {e}")
            self.db.update_project(
                self.project_id,
                {
                    "status": "failed",
                },
            )
            self.db.update_job_status(self.job_id, "failed")
            self._log("core setup failed")

    def _apply_initial_customization(self):
        """Only apply user's initial prompt customization"""
        prompt = self.data["prompt"]
        self._log("Generating a concept of a plan")

        code_service = CodeService(self.project_id, self.job_id, self.user_context, manual_sandbox_termination=True)
        code_service._create_sandbox(repo_dir=code_service.repo_dir)

        self._add_brainstorm_docs_to_repo(code_service, prompt)

        self._log("Starting initial code implementation")
        MAX_ITERATAIONS = 20
        try:
            for iteration in range(MAX_ITERATAIONS):
                try:
                    todo_content = code_service._read_file_from_sandbox("todo.md")
                    open_todo_count = len(re.findall(r'- \[ \]', todo_content))
                    solved_todo_count = len(re.findall(r'- \[x\]', todo_content))
                    print(f'open todos: {open_todo_count} solved todos: {solved_todo_count}')
                    if open_todo_count == 0 and solved_todo_count > 0:
                        print(f"no open todos found after iteration {iteration+1} -> leaving the initial implementation")
                        break

                    print(f"retrying implementation (iteration {iteration+1})")
                    result = code_service.run(
                        IMPLEMENT_TODO_LIST_PROMPT,
                        auto_enhance_context=False
                    )
                except Exception as e:
                    self._log(f"retry iteration {iteration+1} failed: {str(e)}", "warning")
                    continue

            self._submit_successful_project_creation_commit(code_service)
            self._log("Maschine initial code writing complete")
        except Exception as e:
            print(f'initial code writing failed: {e}')
            self._log(f"initial code writing failed: {str(e)}", "error")
        finally:
            code_service.terminate_sandbox()

    def _generate_project_name(self):
        project_name = generate_project_name(self.data["prompt"])
        self.project_name = sanitize_project_name(project_name)
        self._log(message=f"Generated project name: {self.project_name}")
        self.db.update_project(self.project_id, dict(name=project_name))

    def _add_brainstorm_docs_to_repo(self, code_service: CodeService, prompt: str):
        print("Adding brainstormed docs to repo")
        try:
            context = CodeContextEnhancer().get_relevant_context(prompt)
            print("got context, now sending prompt to reasoning model")
            create_spec = CREATE_SPEC_PROMPT.format(context=context, prompt=prompt)
            spec_content, spec_reasoning = send_prompt_to_reasoning_model(create_spec)
            print(f"Received spec content: {spec_content}\nReasoning: {spec_reasoning}")
            code_service._add_file_to_repo_dir("spec.md", spec_content)

            create_prompt_plan = CREATE_PROMPT_PLAN_PROMPT.format(spec=spec_content)
            prompt_plan_content, plan_reasoning = send_prompt_to_reasoning_model(create_prompt_plan)
            print(f"Received plan content: {prompt_plan_content}\nReasoning: {plan_reasoning}")
            code_service._add_file_to_repo_dir("prompt_plan.md", prompt_plan_content)

            todo = CREATE_TODO_LIST_PROMPT.format(plan=prompt_plan_content)
            todo_content, todo_reasoning = send_prompt_to_reasoning_model(todo)
            print(f"Received todo content: {todo_content}\nReasoning: {todo_reasoning}")
            code_service._add_file_to_repo_dir("todo.md", content=todo_content)

            code_service._create_commit("Add spec, plan, and todo list")
            code_service._sync_git_changes()
        except Exception as e:
            print(f"Error occurred while creating todo list: {e}")
            code_service._create_commit("Add spec, plan, and todo list")
            code_service._sync_git_changes()
            raise e

    def _setup_github_repo(self):
        self._log("Creating GitHub repository")
        self.github_api = GithubApi(
            self.job_id, self.project_name, username=self.user_context["username"]
        )
        self.repo_name = self.github_api.create_repo()
        self.github_api.copy_template_to_repo()
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

    def _submit_successful_project_creation_commit(self, code_service: CodeService):
        code_service._create_commit(SETUP_COMPLETE_COMMIT_MESSAGE)
        code_service._sync_git_changes()
        code_service._create_build_and_poll_status_async()

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
