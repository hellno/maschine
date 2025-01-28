import os
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend.integrations.db import Database
from backend.integrations.github_api import clone_repo_to_dir
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

        # Get project details and clone repo
        project = self.db.get_project(self.project_id)
        repo_url = project["repo_url"]
        clone_repo_to_dir(repo_url, repo_dir)

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
            model="r1",
            editor_model="deepseek/deepseek-chat",
            # weak_model="deepseek/deepseek-chat",
        )
        coder = Coder.create(
            io=io,
            fnames=fnames,
            main_model=model,
            read_only_fnames=read_only_fnames,
        )

        print(f"[update_code] Running Aider with prompt: {self.prompt}")
        try:
            aider_result = coder.run(self.prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")

        except Exception as e:
            error_msg = f"Aider run failed: {str(e)}"
            print(f"[update_code] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            return error_msg
