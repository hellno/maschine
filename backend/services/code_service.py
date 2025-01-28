import os
import git
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend.integrations.db import Database
from backend.integrations.github_api import (
    clone_repo_to_dir,
    configure_git_user_for_repo,
)
import tempfile

DEFAULT_PROJECT_FILES = ["src/components/Frame.tsx", "src/lib/constants.ts"]


class CodeService:
    def __init__(self, project_id: str, job_id: str, prompt: str, user_payload: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.prompt = prompt
        self.user_payload = user_payload

        self.db = Database()

    def run(self):
        repo_dir = tempfile.mkdtemp()
        try:
            # Get project details and clone repo
            project = self.db.get_project(self.project_id)
            repo_url = project["repo_url"]
            clone_repo_to_dir(repo_url, repo_dir)
            configure_git_user_for_repo(git.Repo(repo_dir))

            # Set up file paths
            fnames = [os.path.join(repo_dir, f) for f in DEFAULT_PROJECT_FILES]
            llm_docs_dir = os.path.join(repo_dir, "llm_docs")
            read_only_fnames = []
            if os.path.exists(llm_docs_dir):
                read_only_fnames = [
                    os.path.join(llm_docs_dir, f)
                    for f in os.listdir(llm_docs_dir)
                    if os.path.isfile(os.path.join(llm_docs_dir, f))
                ]

            io = InputOutput(yes=True, root=repo_dir)
            model = Model(
                # model="r1",
                model="sonnet",
                # editor_model="deepseek/deepseek-chat",
            )
            coder = Coder.create(
                io=io,
                fnames=fnames,
                main_model=model,
                read_only_fnames=read_only_fnames,
            )

            print(f"[update_code] Running Aider with prompt: {self.prompt}")
            self.db.update_job_status(self.job_id, "running")

            aider_result = coder.run(self.prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")

            # Git operations
            try:
                repo = git.Repo(repo_dir)
                repo.git.add(A=True)
                repo.git.commit("-m", f"Auto update: {self.prompt[:50]}...")
                repo.git.push("origin", "main")
            except git.GitCommandError as e:
                print(f"[update_code] Git operation skipped: {str(e)}")
                # Continue execution - don't treat this as a fatal error

            self.db.update_job_status(self.job_id, "completed")
            return {"status": "success", "result": aider_result}

        except Exception as e:
            error_msg = f"Aider run failed: {str(e)}"
            print(f"[update_code] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

        finally:
            # Cleanup temporary directory
            import shutil

            shutil.rmtree(repo_dir, ignore_errors=True)
