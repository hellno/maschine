import os
import modal
from typing import Optional, Tuple
import git
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend import config
from backend.modal import base_image
from backend.integrations.db import Database
from backend.integrations.github_api import (
    clone_repo_url_to_dir,
    configure_git_user_for_repo,
)
import tempfile

from backend.types import UserContext

DEFAULT_PROJECT_FILES = ["src/components/Frame.tsx", "src/lib/constants.ts"]

#ai! sandbox should be a instance variable
# and add a method to terminate the sandbox
class CodeService:
    def __init__(
        self,
        project_id: str,
        job_id: str,
        prompt: str,
        user_context: Optional[UserContext],
        manual_sandbox_termination: bool = False,
    ):
        self.project_id = project_id
        self.job_id = job_id
        self.prompt = prompt
        self.user_context = user_context
        self.manual_sandbox_termination = manual_sandbox_termination
        self.db = Database()

    def run(self):
        repo_dir = tempfile.mkdtemp()
        try:
            project = self.db.get_project(self.project_id)
            repo_url = project["repo_url"]
            repo = clone_repo_url_to_dir(repo_url, repo_dir)
            configure_git_user_for_repo(repo)

            self._sync_git_changes(repo)

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
            has_errors, logs = self.run_build_in_sandbox(repo_dir)

            if has_errors:
                error_fix_prompt = get_error_fix_prompt_from_logs(logs)
                print("[update_code] Running Aider again to fix build errors")

                # Run another round of fixes
                aider_result = coder.run(error_fix_prompt)
                print(
                    f"[update_code] Fix attempt result (truncated): {aider_result[:250]}"
                )

                # Verify the fixes worked
                has_errors, logs = self.run_build_in_sandbox(
                    repo_dir, terminate_on_success=True
                )
                if has_errors:
                    print("[update_code] Build errors persist after fix attempt")
                    self.db.add_log(
                        self.job_id,
                        "backend",
                        "Build errors could not be automatically fixed",
                    )

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

    def _sync_git_changes(self, repo: git.Repo):
        """Sync any pending git changes with the remote repository."""
        try:
            commits_behind, commits_ahead = repo.git.rev_list(
                "--left-right", "--count", "origin/main...main"
            ).split()
            if int(commits_ahead) > 0:
                print(f"[update_code] Pushing {commits_ahead} pending commits...")
                repo.git.push("origin", "main")
        except git.GitCommandError as e:
            print(f"[update_code] Git status check skipped: {str(e)}")

    def run_build_in_sandbox(
        self, repo_dir: str, terminate_on_success: bool = False
    ) -> Tuple[bool, str]:
        """Run build commands in an isolated Modal sandbox."""
        try:
            logs = []
            app = modal.App.lookup(config.APP_NAME)
            sandbox = modal.Sandbox.create(
                app=app,
                image=base_image.add_local_dir(repo_dir, remote_path="/repo"),
                cpu=2,
                memory=4096,
                workdir="/repo",
                timeout=config.TIMEOUTS["BUILD"],
            )
            sandbox.set_tags({"project_id": self.project_id, "job_id": self.job_id})

            print("[update_code] Running install command")
            process = sandbox.exec("pnpm", "install")
            for line in process.stdout:
                print("[install]", line.strip())
            process.wait()

            print("[update_code] Running build command")
            process = sandbox.exec("pnpm", "build")
            for line in process.stdout:
                logs.append(line.strip())
                print("[build]", line.strip())
            for line in process.stderr:
                logs.append(line.strip())
                print("[build ERR]", line.strip())
            process.wait()

            has_error_in_logs = any(
                "error" in line.lower()
                or "failed" in line.lower()
                or "exited with 1" in line.lower()
                for line in logs
            )

            logs_cleaned = clean_log_lines(logs)
            logs_str = "\n".join(logs_cleaned)
            returncode = process.returncode
            print(
                f"sandbox results: has_error_in_logs {has_error_in_logs} returncode {returncode} logs_str {logs_str} "
            )
            if terminate_on_success and not self.manual_sandbox_termination:
                print("[update_code] Terminating sandbox after successful build")
                sandbox.terminate()

            return has_error_in_logs, logs_str

        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

        finally:
            if "sandbox" in locals():
                sandbox.terminate()


def get_error_fix_prompt_from_logs(logs: str) -> str:
    """Extract a prompt from build logs to fix errors."""
    return f"""
    The previous changes caused build errors. Please fix them.
    Here are the build logs showing the errors:
    
    {logs}
    
    Please analyze these errors and make the necessary corrections to fix the build.
    """


def clean_log_lines(logs: list[str]) -> list[str]:
    """Clean up log lines for display."""
    urls_to_skip = ["nextjs.org/telemetry", "vercel.com/docs/analytics"]

    return [
        line
        for line in logs
        if line
        and not line.startswith("warning")
        and not any(url in line for url in urls_to_skip)
    ]
