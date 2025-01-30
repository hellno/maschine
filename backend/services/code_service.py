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


class CodeService:
    def __init__(
        self,
        project_id: str,
        job_id: str,
        user_context: Optional[UserContext],
        manual_sandbox_termination: bool = False,
    ):
        self.project_id = project_id
        self.job_id = job_id
        self.user_context = user_context
        self.manual_sandbox_termination = manual_sandbox_termination

        self.sandbox = None
        self.repo_dir = None
        self.db = None
        self.is_setup = False
        self.base_image_with_deps = None

        self._setup()

    def run(self, prompt: str):
        try:
            # Extract Aider-specific code into a dedicated function
            coder = self._create_aider_coder()
            
            print(f"[update_code] Running Aider with prompt: {prompt}")
            self.db.update_job_status(self.job_id, "running")

            aider_result = coder.run(prompt)
            print(f"[update_code] Aider result (truncated): {aider_result[:250]}")
            has_errors, logs = self._run_build_in_sandbox()

            if has_errors:
                error_fix_prompt = get_error_fix_prompt_from_logs(logs)
                print("[update_code] Running Aider again to fix build errors")

                aider_result = coder.run(error_fix_prompt)
                print(
                    f"[update_code] Fix attempt result (truncated): {aider_result[:250]}"
                )

                has_errors, logs = self._run_build_in_sandbox(
                    terminate_after_build=True
                )
                if has_errors:
                    print("[update_code] Build errors persist after fix attempt")
                    self.db.add_log(
                        self.job_id,
                        "backend",
                        "Build errors could not be automatically fixed",
                    )

            self._sync_git_changes()
            self.db.update_job_status(self.job_id, "completed")
            return {"status": "success", "result": aider_result}

        except Exception as e:
            print('exception in run', e)
            error_msg = f"aider run failed: {str(e)}"
            print(f"[update_code] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise
            # return {"status": "error", "error": error_msg}

    def terminate_sandbox(self):
        """Safely terminate the sandbox if it exists."""
        if self.sandbox:
            try:
                print(f"[update_code] Terminating sandbox - job id {self.job_id}")
                self.sandbox.terminate()
                self.sandbox = None
                print("[update_code] Sandbox terminated")
            except Exception as e:
                print(f"Error terminating sandbox job id {self.job_id}: {str(e)}")

    def _setup(self):
        if self.is_setup:
            return

        print("[update_code] Setting up CodeService")
        self.db = Database()
        self.repo_dir = tempfile.mkdtemp()

        project = self.db.get_project(self.project_id)
        repo_url = project["repo_url"]
        repo = clone_repo_url_to_dir(repo_url, self.repo_dir)
        configure_git_user_for_repo(repo)

        self.is_setup = True
        print("[update_code] CodeService setup complete")

    def _sync_git_changes(self):
        """Sync any pending git changes with the remote repository."""
        try:
            print("[update_code] Syncing git changes in repo dir", self.repo_dir)
            repo = git.Repo(self.repo_dir)
            # commits_behind, commits_ahead = repo.git.rev_list(
            #     "--left-right", "--count", "origin/main...main"
            # ).split()
            # print(
            #     f"[update_code] Commits behind: {commits_behind}, ahead: {commits_ahead}"
            # )
            # if int(commits_ahead) > 0:
            #     print(f"[update_code] Pushing {commits_ahead} pending commits...")
            repo.git.push("origin", "main")
        except git.GitCommandError as e:
            print(f"[update_code] sync git changes failed: {str(e)}")

    def _run_install_in_sandbox(self):
        print("[update_code] Running install command")
        process = self.sandbox.exec("pnpm", "install")
        for line in process.stdout:
            print("[install]", line.strip())
        process.wait()

    def _run_build_in_sandbox(
        self, terminate_after_build: bool = False
    ) -> Tuple[bool, str]:
        """Run build commands in an isolated Modal sandbox."""
        try:
            self._create_sandbox(repo_dir=self.repo_dir)
            
            logs = []
            print("[build] Current git status:")
            git_status = self.sandbox.exec("git", "status")
            for line in git_status.stdout:
                print("[git]", line.strip())

            print("[build] Latest commit:")
            git_log = self.sandbox.exec("git", "log", "-1", "--oneline")
            for line in git_log.stdout:
                print("[git]", line.strip())

            process = self.sandbox.exec("pnpm", "install")
            for line in process.stdout:
                print("[base install]", line.strip())
            process.wait()

            print("[build] Running build command")
            process = self.sandbox.exec("pnpm", "build")
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
            if terminate_after_build and not self.manual_sandbox_termination:
                print("[update_code] Terminating sandbox after build")
                self.terminate_sandbox()
            return has_error_in_logs, logs_str

        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

    def _create_base_image_with_deps(self, repo_dir: str) -> modal.Image:
        """Create a base image with dependencies installed."""
        print("[update_code] Creating base sandbox for dependency installation")
        app = modal.App.lookup(config.APP_NAME)
        base_sandbox = modal.Sandbox.create(
            app=app,
            image=base_image.add_local_dir(repo_dir, remote_path="/repo"),
            cpu=2,
            memory=4096,
            workdir="/repo",
            timeout=config.TIMEOUTS["BUILD"],
        )
        image = None
        try:
            print("[update_code] Installing dependencies in base sandbox")
            process = base_sandbox.exec("pnpm", "install")
            for line in process.stdout:
                print("[base install]", line.strip())
            process.wait()

            if process.returncode != 0:
                raise Exception("Base dependency installation failed")

            print("[update_code] Creating filesystem snapshot")
            image = base_sandbox.snapshot_filesystem()
        finally:
            base_sandbox.terminate()
            return image

    def _create_sandbox(self, repo_dir: str):
        """Create a sandbox using the cached base image if available."""
        app = modal.App.lookup(config.APP_NAME)

        if not self.base_image_with_deps:
            self.base_image_with_deps = self._create_base_image_with_deps(repo_dir)

        self.sandbox = modal.Sandbox.create(
            app=app,
            image=self.base_image_with_deps.add_local_dir(
                repo_dir, remote_path="/repo"
            ),
            cpu=2,
            memory=4096,
            workdir="/repo",
            timeout=config.TIMEOUTS["BUILD"],
        )
        self.sandbox.set_tags({"project_id": self.project_id, "job_id": self.job_id})
        self._run_install_in_sandbox()
        print("[update_code] Sandbox created")

    def _create_aider_coder(self) -> Coder:
        """Create and configure the Aider coder instance."""
        fnames = [os.path.join(self.repo_dir, f) for f in DEFAULT_PROJECT_FILES]
        llm_docs_dir = os.path.join(self.repo_dir, "llm_docs")
        read_only_fnames = []
        if os.path.exists(llm_docs_dir):
            read_only_fnames = [
                os.path.join(llm_docs_dir, f)
                for f in os.listdir(llm_docs_dir)
                if os.path.isfile(os.path.join(llm_docs_dir, f))
            ]

        io = InputOutput(yes=True, root=self.repo_dir)
        model = Model(**config.AIDER_CONFIG["MODEL"])
        return Coder.create(
            io=io,
            fnames=fnames,
            main_model=model,
            read_only_fnames=read_only_fnames,
            **config.AIDER_CONFIG["CODER"],
        )


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
