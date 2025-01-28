import os
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend.integrations.db import Database
from backend.integrations.github_api import clone_repo_to_dir

DEFAULT_PROJECT_FILES = ["src/components/Frame.tsx", "src/lib/constants.ts"]

class CodeService:
    def __init__(self, project_id: str, job_id: str, prompt: str, user_payload: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.prompt = prompt
        self.user_payload = user_payload
        
        self.db = Database()

    def run():
        # ai! todo:
        # 1. fix the paths, we just need one temporary directory 
        # 2. clone the github repo clone_repo_to_dir(repo_url, dir_path)
        # 2. asdasdasd
        
        
        fnames = [
            os.path.join(sandbox_test_cmd.workdir, f) for f in DEFAULT_PROJECT_FILES
        ]
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
            model="r1",
            weak_model="deepseek/deepseek-chat",
            editor_model="deepseek/deepseek-chat",
        )
        coder = Coder.create(
            io=io,
            fnames=fnames,
            main_model=model,
            read_only_fnames=read_only_fnames,
        )

        print(f"[update_code] Running Aider with prompt: {prompt}")
        try:
            aider_result = coder.run(prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")

        except Exception as e:
            error_msg = f"Aider run failed: {str(e)}"
            print(f"[update_code] {error_msg}")
            self.db.add_log(job_id, "backend", error_msg)
            self.db.update_job_status(job_id, "failed", error_msg)
            return error_msg
