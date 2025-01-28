import os
from typing import Optional
import git
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend import config
from backend.integrations.db import Database
from backend.integrations.github_api import (
    clone_repo_url_to_dir,
    configure_git_user_for_repo,
)
import tempfile

from backend.types import UserContext

DEFAULT_PROJECT_FILES = ["src/components/Frame.tsx", "src/lib/constants.ts"]


class CodeService:
    def __init__(
        self,
        project_id: str,
        job_id: str,
        prompt: str,
        user_context: Optional[UserContext],
    ):
        self.project_id = project_id
        self.job_id = job_id
        self.prompt = prompt
        self.user_context = user_context

        self.db = Database()

    def run(self):
        repo_dir = tempfile.mkdtemp()
        try:
            project = self.db.get_project(self.project_id)
            repo_url = project["repo_url"]
            repo = clone_repo_url_to_dir(repo_url, repo_dir)
            configure_git_user_for_repo(repo)

            # ai! encapsulate into standalone class function of CodeService
            try:
                commits_behind, commits_ahead = repo.git.rev_list(
                    "--left-right", "--count", "origin/main...main"
                ).split()
                if int(commits_ahead) > 0:
                    print(f"[update_code] Pushing {commits_ahead} pending commits...")
                    repo.git.push("origin", "main")
            except git.GitCommandError as e:
                print(f"[update_code] Git status check skipped: {str(e)}")

            # Set up file paths
            fnames = [os.path.join(repo_dir, f) for f in DEFAULT_PROJECT_FILES]
            llm_docs_dir = os.path.join(repo_dir, "llm_docs")
            read_only_fnames = []
            # if os.path.exists(llm_docs_dir):
            #     read_only_fnames = [
            #         os.path.join(llm_docs_dir, f)
            #         for f in os.listdir(llm_docs_dir)
            #         if os.path.isfile(os.path.join(llm_docs_dir, f))
            #     ]

            io = InputOutput(yes=True, root=repo_dir)
            model = Model(**config.AIDER_CONFIG["MODEL"])
            coder = Coder.create(
                io=io,
                fnames=fnames,
                main_model=model,
                read_only_fnames=read_only_fnames,
                **config.AIDER_CONFIG["CODER"],
            )

            print(f"[update_code] Running Aider with prompt: {self.prompt}")
            self.db.update_job_status(self.job_id, "running")

            aider_result = coder.run(self.prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")

            try:
                repo = git.Repo(repo_dir)
                if repo.is_dirty():
                    repo.git.add(A=True)
                    repo.git.commit("-m", f"auto update: {self.prompt[:50]}...")
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

    def run_build_in_sandbox(self):
        # ai! todo: implement this function
        # we can run sandbox code via modal like this: https://modal.com/docs/reference/modal.Sandbox#snapshot_filesystem
        # https://modal.com/docs/guide/sandbox
        # we can re-use the same environment that we have for the whole app
        # app = modal.App.lookup("my-app")
        # modal.Sandbox.create("echo", "hi", app=app)
        # more example code:
        # import modal
        # sb = modal.Sandbox.create(app=app)
        # p = sb.exec("python", "-c", "print('hello')")
        # print(p.stdout.read())
        # p = sb.exec("bash", "-c", "for i in {1..10}; do date +%T; sleep 0.5; done")
        # for line in p.stdout:
        #     # Avoid double newlines by using end="".
        #     print(line, end="")
        # sb.terminate()
        pass