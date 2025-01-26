import os
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

DEFAULT_PROJECT_FILES = ["src/components/Frame.tsx", "src/lib/constants.ts"]

class CodeService:
    def __init__(self, project_id: str, job_id: str, prompt: str, user_payload: dict):
        self.project_id = project_id
        self.job_id = job_id
        self.prompt = prompt
        self.user_payload = user_payload

    def run():
        # todo:
        # 1. fix the paths
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
            auto_test=True,
            main_model=model,
            test_cmd=sandbox_test_cmd,
            read_only_fnames=read_only_fnames,
        )

        print(f"[update_code] Running Aider with prompt: {prompt}")
        try:
            aider_result = coder.run(prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")

            # Handle any pnpm commands in the Aider output
            _handle_pnpm_commands(aider_result, sandbox, git_service, job_id, db)

        except Exception as e:
            error_msg = f"Aider run failed: {str(e)}"
            print(f"[update_code] {error_msg}")
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", error_msg)
            sandbox.terminate()
            return error_msg

        # Push changes if any
        if not git_service.safe_push("Automated update from Aider"):
            db.add_log(job_id, "git", "Warning: Failed to push changes to remote")
