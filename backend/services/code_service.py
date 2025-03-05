import os
import modal
import time
import threading
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
from backend.services.context_enhancer import CodeContextEnhancer

DEFAULT_PROJECT_FILES = [
    "src/components/Frame.tsx",
    "src/lib/constants.ts",
    "src/app/opengraph-image.tsx",
    "todo.md",
]

READONLY_FILES = [
    "prompt_plan.md",
    "llm_docs/frames.md",
    # "plan.md",
    # "spec.md",
]


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
        self.db: Optional[Database] = None
        self.is_setup = False
        self.base_image_with_deps = None

        self._setup()

    def run(self, prompt: str, auto_enhance_context: bool = True) -> dict:
        """Run the Aider coder with the given prompt."""
        if not self.db:
            raise ValueError("Database not initialized")

        try:
            coder = self._create_aider_coder()

            print(f"[code_service] Running Aider with prompt: {prompt}")
            self.db.update_job_status(self.job_id, "running")
            if auto_enhance_context:
                prompt = self._enhance_prompt_with_context(prompt)

            # Retry logic with 3 attempts
            max_retries = 3
            retry_delay = 10  # seconds between retries
            aider_result = None
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Run with 60 second timeout per attempt
                    result = [None]  # Use list to store result from thread
                    exception = []
                    
                    def run_aider():
                        try:
                            result[0] = coder.run(prompt)
                        except Exception as e:
                            exception.append(e)
                    
                    thread = threading.Thread(target=run_aider)
                    thread.start()
                    thread.join(timeout=60)
                    
                    if thread.is_alive():
                        # Thread is still running after timeout
                        raise TimeoutError("coder.run timed out after 60 seconds")
                    
                    if exception:
                        # Re-raise the exception caught in the thread
                        raise exception[0]
                        
                    aider_result = result[0]
                    break
                except TimeoutError as e:
                    last_exception = e
                    error_msg = f"Timeout after 60 seconds (attempt {attempt+1}/{max_retries})"
                    print(f"[code_service] {error_msg}")
                    self.db.add_log(self.job_id, "backend", error_msg)
                    
                    if attempt < max_retries - 1:
                        print(f"Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt+1} failed, retrying in {retry_delay} seconds...")
                        self.db.add_log(
                            self.job_id,
                            "backend",
                            f"Attempt {attempt+1} failed: {str(e)}. Retrying..."
                        )
                        time.sleep(retry_delay)
                    else:
                        error_msg = f"Failed after {max_retries} attempts: {str(last_exception)}"
                        print(f"[code_service] {error_msg}")
                        self.db.add_log(self.job_id, "backend", error_msg)
                        self.db.update_job_status(self.job_id, "failed", error_msg)
                        self.terminate_sandbox()
                        return {"status": "error", "error": error_msg}

            if not aider_result:
                error_msg = "All attempts failed - no aider result"
                print(f"[code_service] {error_msg}")
                self.db.add_log(self.job_id, "backend", error_msg)
                self.db.update_job_status(self.job_id, "failed", error_msg)
                self.terminate_sandbox()
                return {"status": "error", "error": error_msg}

            print(f"[code_service] Aider result (truncated): {aider_result[:250]}")
            _handle_pnpm_commands(aider_result, self.sandbox)
            has_errors, logs = self._run_build_in_sandbox()

            if has_errors:
                error_fix_prompt = get_error_fix_prompt_from_logs(logs)
                print("[code_service] Running Aider again to fix build errors")

                aider_result = coder.run(error_fix_prompt)
                print(
                    f"[code_service] Fix attempt result (truncated): {aider_result[:250]}"
                )

                has_errors, logs = self._run_build_in_sandbox(
                    terminate_after_build=True
                )
                if has_errors:
                    print("[code_service] Build errors persist after fix attempt")
                    self.db.add_log(
                        self.job_id,
                        "backend",
                        "Build errors could not be automatically fixed",
                    )

            self._sync_git_changes()
            self._create_build_and_poll_status_async()
            self.db.update_job_status(self.job_id, "completed")
            return {"status": "success", "result": aider_result, "build_logs": logs}

        except Exception as e:
            print("exception in run", e)
            error_msg = f"aider run failed: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise

    def terminate_sandbox(self):
        """Safely terminate the sandbox if it exists."""
        if self.sandbox:
            try:
                print(f"[code_service] Terminating sandbox - job id {self.job_id}")
                self.sandbox.terminate()
                self.sandbox = None
                print("[code_service] Sandbox terminated")
            except Exception as e:
                print(f"Error terminating sandbox job id {self.job_id}: {str(e)}")

    def _enhance_prompt_with_context(self, prompt: str) -> str:
        try:
            context = CodeContextEnhancer().get_relevant_context(prompt)
            return f"additional context {context}\n\nprompt {prompt}"
        except Exception as e:
            print(f"[code_service] Context enhancement failed: {str(e)}")
        return prompt

    def _add_file_to_repo_dir(self, filename: str, content: str) -> None:
        context_file = os.path.join(self.repo_dir, filename)
        os.makedirs(os.path.dirname(context_file), exist_ok=True)
        with open(context_file, "w") as f:
            f.write(content)

    def _read_file_from_sandbox(self, filename: str) -> str:
        """Read file contents from sandbox using cat command"""
        if not self.sandbox:
            print(f'error reading file from sandbox {filename}, sandbox not initialized')
            return ""

        try:
            # Execute cat command to read file
            process = self.sandbox.exec("cat", filename)
            logs, exit_code = self.parse_sandbox_process(process)

            if exit_code == 0:
                return "\n".join(logs)
            return ""

        except Exception as e:
            print(f"Error reading {filename} from sandbox: {str(e)}")
            return ""

    def _setup(self):
        if self.is_setup:
            return

        print("[code_service] Setting up CodeService")
        self.db = Database()
        self.repo_dir = tempfile.mkdtemp()

        project = self.db.get_project(self.project_id)
        repo_url = project["repo_url"]
        repo = clone_repo_url_to_dir(repo_url, self.repo_dir)
        configure_git_user_for_repo(repo)

        self.is_setup = True
        print("[code_service] CodeService setup complete")

    def _sync_git_changes(self):
        """Sync any pending git changes with the remote repository."""
        try:
            print("[code_service] Syncing git changes in repo dir", self.repo_dir)
            repo = git.Repo(path=self.repo_dir)
            if repo.is_dirty():
                print("[code_service] Committing changes to git")
                self._create_commit("automatic changes")

            # Push changes
            repo.git.push("origin", "main")
        except git.GitCommandError as e:
            print(f"[code_service] sync git changes failed: {str(e)}")

    def _create_commit(self, message: str):
        repo = git.Repo(path=self.repo_dir)
        repo.git.add(A=True)
        repo.git.commit("-m", message, "--allow-empty")

    def _run_install_in_sandbox(self):
        if not self.sandbox:
            print('error running install in sandbox, sandbox not initialized')
            return

        print("[code_service] Running install command")
        process = self.sandbox.exec("pnpm", "install")
        logs, exit_code = self.parse_sandbox_process(process)
        return exit_code

    def get_git_repo_status(self) -> Tuple[bool, bool]:
        if not self.sandbox:
            print('error getting git repo status, sandbox not initialized')
            return False, False

        git_status = self.sandbox.exec("git", "status")
        status_logs, _ = self.parse_sandbox_process(git_status)
        print("[build] Current git status:", status_logs)
        no_new_commits = 'Your branch is up to date'
        no_pending_changes = 'nothing to commit'
        has_new_commits = no_new_commits not in status_logs
        has_pending_changes = no_pending_changes not in status_logs

        return has_new_commits, has_pending_changes

    def _run_build_in_sandbox(
        self, terminate_after_build: bool = False
    ) -> Tuple[bool, str]:
        """Run build commands in an isolated Modal sandbox."""
        try:
            self._create_sandbox(repo_dir=self.repo_dir)

            logs = []

            has_new_commits, has_pending_changes = self.get_git_repo_status()
            if not has_new_commits and not has_pending_changes:
                print("[build] No new commits or pending changes. skipping to build again")
                return False, "No new commits or pending changes"

            git_log = self.sandbox.exec("git", "log", "-1", "--oneline")
            log_lines, _ = self.parse_sandbox_process(git_log)
            logs.extend(log_lines)
            print("[build] Latest commit:", log_lines)

            install_process = self.sandbox.exec("pnpm", "install")
            install_logs, install_code = self.parse_sandbox_process(install_process)
            logs.extend(install_logs)

            print("[build] Running build command")
            build_process = self.sandbox.exec("pnpm", "build")
            build_logs, build_returncode = self.parse_sandbox_process(build_process)
            logs.extend(build_logs)

            has_error_in_logs = build_returncode == 1 or any(
                "error" in line.lower()
                or "failed" in line.lower()
                or "exited with 1" in line.lower()
                for line in logs
            )

            logs_cleaned = clean_log_lines(logs)
            logs_str = "\n".join(logs_cleaned)
            print(
                f"sandbox results: has_error_in_logs {has_error_in_logs} build return_code {build_returncode} logs_str {logs_str} "
            )
            print(f'terminate_after_build {terminate_after_build} manual_sandbox_termination {self.manual_sandbox_termination}')
            if terminate_after_build and not self.manual_sandbox_termination:
                print("[code_service] Terminating sandbox after build")
                self.terminate_sandbox()
            return has_error_in_logs, logs_str

        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            return {"status": "error", "error": error_msg}

    def _create_base_image_with_deps(self, repo_dir: str) -> modal.Image:
        """Create a base image with dependencies installed."""
        print("[code_service] Creating base sandbox for dependency installation")

        app = modal.App.lookup(config.APP_NAME)
        image = None
        base_sandbox = None

        try:
            base_sandbox = modal.Sandbox.create(
                app=app,
                image=base_image.add_local_dir(repo_dir, remote_path="/repo"),
                cpu=4,
                memory=2048,
                workdir="/repo",
                timeout=config.TIMEOUTS["BUILD"],
            )

            print("[code_service] Installing dependencies in base sandbox")
            process = base_sandbox.exec(
                "pnpm",
                "install",
                "--loglevel",
                "debug",
                "--reporter",
                "ndjson",
            )
            install_logs, exit_code = self.parse_sandbox_process(
                process, prefix="base install"
            )
            # print(
            #     "[code_service] Base install logs:",
            #     "\n".join(install_logs),
            #     "exit code",
            #     exit_code,
            # )
            print("[code_service] base install process completed")

            if exit_code != 0:
                raise Exception("Base dependency installation failed")

            print("[code_service] Creating filesystem snapshot")
            image = base_sandbox.snapshot_filesystem()
            return image

        except Exception as e:
            print(f"[code_service] Base image creation failed: {str(e)}")
            raise
        finally:
            if base_sandbox:
                print("[code_service] Cleaning up base sandbox")
                base_sandbox.terminate()

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
            memory=1024,
            workdir="/repo",
            # timeout=config.TIMEOUTS["BUILD"],
        )
        self.sandbox.set_tags({"project_id": self.project_id, "job_id": self.job_id})
        self._run_install_in_sandbox()
        print("[code_service] Sandbox created")

    def parse_sandbox_process(self, process, prefix="") -> tuple[list, int]:
        """Safely parse stdout/stderr from a sandbox process using Modal's StreamReader."""
        logs = []
        exit_code = -1

        try:
            # Handle stdout - check if bytes need decoding
            for line in process.stdout:
                try:
                    if isinstance(line, bytes):  # Handle both str and bytes
                        decoded = line.decode("utf-8", "ignore").strip()
                    else:
                        decoded = str(line).strip()  # Convert to string if needed
                    logs.append(decoded)
                    # print(f"[{prefix}] {decoded}")
                except UnicodeDecodeError as ude:
                    error_msg = f"Decode error: {str(ude)}"
                    logs.append(error_msg)
                    print(f"[{prefix} ERR] {error_msg}")

            # Handle stderr the same way
            for line in process.stderr:
                try:
                    if isinstance(line, bytes):
                        decoded = line.decode("utf-8", "ignore").strip()
                    else:
                        decoded = str(line).strip()
                    logs.append(decoded)
                    # print(f"[{prefix} ERR] {decoded}")
                except UnicodeDecodeError as ude:
                    error_msg = f"Decode error: {str(ude)}"
                    logs.append(error_msg)
                    print(f"[{prefix} ERR] {error_msg}")

            # Get exit code after reading all output
            exit_code = process.wait()

        except Exception as e:
            error_msg = f"Process handling failed: {str(e)}"
            logs.append(error_msg)
            print(f"[{prefix} CRITICAL] {error_msg}")

        return logs, exit_code

    def _create_aider_coder(self) -> Coder:
        """Create and configure the Aider coder instance."""
        fnames = [os.path.join(self.repo_dir, f) for f in DEFAULT_PROJECT_FILES]
        read_only_fnames = READONLY_FILES

        io = InputOutput(yes=True, root=self.repo_dir)
        model = Model(**config.AIDER_CONFIG["MODEL"])
        return Coder.create(
            io=io,
            fnames=fnames,
            main_model=model,
            read_only_fnames=read_only_fnames,
            **config.AIDER_CONFIG["CODER"],
        )

    def _get_latest_commit_sha(self) -> str:
        repo = git.Repo(path=self.repo_dir)
        return repo.head.commit.hexsha

    def _create_build_and_poll_status_async(self):
        has_new_commits, has_pending_changes = self.get_git_repo_status()
        if not has_new_commits:
            print("No new commits or pending changes found")
            return

        commit_hash = self._get_latest_commit_sha()
        build_id = self.db.create_build(
            self.project_id, commit_hash, status="submitted"
        )
        self._start_build_polling(build_id, commit_hash)

    def _start_build_polling(self, build_id: str, commit_hash: str):
        """Start asynchronous polling for build status"""
        try:
            print(f"[code_service] Starting build polling for build {build_id}")
            # Start an asynchronous function to poll the build status
            poll_build_status_spawn = modal.Function.from_name(config.APP_NAME, f"{config.MODAL_POLL_BUILD_FUNCTION_NAME}_spawn")
            poll_build_status_spawn.spawn(project_id=self.project_id, build_id=build_id, commit_hash=commit_hash)
            print(f"[code_service] Build polling started for {build_id} with commit {commit_hash}")

        except Exception as e:
            error_msg = f"Failed to start build polling: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)

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
    phrases_to_skip = [
        "nextjs.org/telemetry",
        "vercel.com/docs/analytics",
        "[Upstash Redis]",
        "metadataBase property in metadata export"
    ]
    return [
        line
        for line in logs
        if line
        and not line.startswith("warning")
        and not any(url in line for url in phrases_to_skip)
    ]


def _handle_pnpm_commands(
    aider_result: str,
    sandbox: modal.Sandbox,
) -> None:
    """Parse and execute pnpm/npm install commands from Aider output"""
    import re

    pattern = r"```bash[\s\n]*(?:pnpm add|npm install(?: --save)?)\s+([^\n`]*)```"
    matches = list(re.finditer(pattern, aider_result, re.DOTALL))

    print(
        f"[code_service] Found {len(matches)} package install commands in aider output"
    )

    for match in matches:
        packages = match.group(1).strip()
        if not packages:
            continue

        try:
            print(f"[code_service] Installing packages: {packages}")
            install_proc = sandbox.exec("pnpm", "add", *packages.split())

            # Use the new parsing utility
            logs, exit_code = CodeService.parse_sandbox_process(install_proc)

            if exit_code != 0:
                print(f"[code_service] pnpm add failed with code {exit_code}")
                print("Installation logs:", "\n".join(logs))

        except Exception as e:
            error_msg = f"Error installing packages {packages}: {e}"
            print(f"[code_service] {error_msg}")
