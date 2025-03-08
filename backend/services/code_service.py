import os
import modal
import time
import threading
import multiprocessing
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
from backend.utils.package_commands import handle_package_install_commands
from backend.exceptions import (
    CodeServiceError, SandboxError, SandboxCreationError, SandboxTerminationError,
    GitError, GitCloneError, GitPushError,
    BuildError, InstallError, CompileError,
    AiderError, AiderTimeoutError, AiderExecutionError
)

DEFAULT_PROJECT_FILES = [
    "src/components/Frame.tsx",
    "src/lib/constants.ts",
    "src/app/opengraph-image.tsx",
    "todo.md",
]

READONLY_FILES = [
    "prompt_plan.md",
    "llm_docs/frames.md",
    "spec.md",
]

def parse_sandbox_process(process, prefix="") -> tuple[list, int]:
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
            retry_delay = 15  # seconds between retries
            timeout = 120  # seconds for each attempt

            for attempt in range(max_retries):
                try:
                    # Run for timeout seconds per attempt
                    aider_result = run_with_timeout_and_retries(
                        target=coder.run,
                        args=(prompt,),
                        max_retries=1,  # Individual attempts handled by outer loop
                        retry_delay=retry_delay,
                        timeout=timeout
                    )
                    handle_package_install_commands(
                        aider_result,
                        self.sandbox,
                        parse_sandbox_process
                    )
                    print(f"[code_service] Aider result (truncated): {aider_result[:250]}")
                    break
                except TimeoutError:
                    error_msg = f"Timeout after {timeout} seconds (attempt {attempt+1}/{max_retries})"
                    print(f"[code_service] {error_msg}")

                    if attempt < max_retries - 1:
                        print(f"Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt+1} failed, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        error_msg = f"Failed after {max_retries} attempts: {str(e)}"
                        print(f"[code_service] {error_msg}")
                        self.db.add_log(self.job_id, "backend", error_msg)
                        self.db.update_job_status(self.job_id, "failed", error_msg)
                        self.terminate_sandbox()
                        return {"status": "error", "error": error_msg}


            has_errors, logs = self._run_build_in_sandbox()

            if has_errors:
                error_fix_prompt = get_error_fix_prompt_from_logs(logs)
                print("[code_service] Running Aider again to fix build errors")

                aider_result = coder.run(error_fix_prompt)
                if aider_result:
                    print(
                        f"[code_service] Fix attempt result (truncated): {aider_result[:250]}"
                )

                has_errors, logs = self._run_build_in_sandbox(
                    terminate_after_build=True
                )
                if has_errors:
                    print("[code_service] Build errors persist after fix attempt")

            self._sync_git_changes()
            self._create_build_and_poll_status_async()
            self.db.update_job_status(self.job_id, "completed")
            return {"status": "success", "build_logs": logs}

        except (AiderTimeoutError, AiderExecutionError) as e:
            error_msg = f"Aider execution failed: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "aider", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise
        except (InstallError, CompileError, BuildError) as e:
            error_msg = f"Build process failed: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise
        except GitError as e:
            error_msg = f"Git operation failed: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "git", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise
        except SandboxError as e:
            error_msg = f"Sandbox operation failed: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "sandbox", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise
        except Exception as e:
            # Fallback for any other exceptions
            error_msg = f"Unexpected error during code generation: {str(e)}"
            print(f"[code_service] {error_msg}")
            self.db.add_log(self.job_id, "backend", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            self.terminate_sandbox()
            raise CodeServiceError(error_msg, self.job_id, self.project_id, e)

    def terminate_sandbox(self):
        """Safely terminate the sandbox if it exists."""
        if self.sandbox:
            try:
                print(f"[code_service] Terminating sandbox - job id {self.job_id}")
                self.sandbox.terminate()
                self.sandbox = None
                print("[code_service] Sandbox terminated")
            except Exception as e:
                error_msg = f"Error terminating sandbox job id {self.job_id}: {str(e)}"
                print(error_msg)
                if hasattr(self, 'job_id') and hasattr(self, 'project_id'):
                    raise SandboxTerminationError(self.job_id, self.project_id, e)
                else:
                    raise SandboxError(
                        "Failed to terminate sandbox",
                        getattr(self, 'job_id', None),
                        getattr(self, 'project_id', None),
                        e
                    )

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
            logs, exit_code = parse_sandbox_process(process)

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

        try:
            project = self.db.get_project(self.project_id)
            repo_url = project["repo_url"]
            repo = clone_repo_url_to_dir(repo_url, self.repo_dir)
            configure_git_user_for_repo(repo)

            self.is_setup = True
            print("[code_service] CodeService setup complete")
        except git.GitCommandError as e:
            raise GitCloneError(self.job_id, self.project_id, e)
        except Exception as e:
            raise CodeServiceError(
                "Failed to set up code service",
                self.job_id,
                self.project_id,
                e
            )

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
            raise GitPushError(self.job_id, self.project_id, e)

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
        logs, exit_code = parse_sandbox_process(process)
        return exit_code

    def get_git_repo_status(self) -> Tuple[bool, bool]:
        if not self.sandbox:
            print('error getting git repo status, sandbox not initialized')
            return False, False

        git_status = self.sandbox.exec("git", "status")
        status_logs, _ = parse_sandbox_process(git_status)
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
            log_lines, _ = parse_sandbox_process(git_log)
            logs.extend(log_lines)
            print("[build] Latest commit:", log_lines)

            install_process = self.sandbox.exec("pnpm", "install")
            install_logs, install_code = parse_sandbox_process(install_process)
            logs.extend(install_logs)

            if install_code != 0:
                logs_str = "\n".join(clean_log_lines(logs))
                raise InstallError(self.job_id, self.project_id, Exception(f"Install failed with code {install_code}: {logs_str}"))

            print("[build] Running build command")
            build_process = self.sandbox.exec("pnpm", "build")
            build_logs, build_returncode = parse_sandbox_process(build_process)
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
                
            if has_error_in_logs and build_returncode != 0:
                raise CompileError(self.job_id, self.project_id, logs_str)
                
            return has_error_in_logs, logs_str

        except (CompileError, InstallError, SandboxError):
            # Already using specific error types, just re-raise
            raise
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during build: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            raise BuildError(self.job_id, self.project_id, e)
        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            self.db.update_job_status(self.job_id, "failed", error_msg)
            raise BuildError(self.job_id, self.project_id, e)

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
                # timeout=config.TIMEOUTS["BUILD"],
            )

            print("[code_service] Installing dependencies in base sandbox")
            process = base_sandbox.exec(
                "pnpm",
                "install",
            )
            install_logs, exit_code = parse_sandbox_process(
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
                logs_str = "\n".join(install_logs)
                raise InstallError(self.job_id, self.project_id, Exception(f"Exit code: {exit_code}, Logs: {logs_str}"))

            print("[code_service] Creating filesystem snapshot")
            image = base_sandbox.snapshot_filesystem()
            return image

        except InstallError:
            raise
        except Exception as e:
            print(f"[code_service] Base image creation failed: {str(e)}")
            raise SandboxCreationError(self.job_id, self.project_id, e)
        finally:
            if base_sandbox:
                print("[code_service] Cleaning up base sandbox")
                try:
                    base_sandbox.terminate()
                except Exception as e:
                    print(f"[code_service] Failed to terminate base sandbox: {str(e)}")

    def _create_sandbox(self, repo_dir: str):
        """Create a sandbox using the cached base image if available."""
        try:
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
        except Exception as e:
            print(f"[code_service] Failed to create sandbox: {str(e)}")
            raise SandboxCreationError(self.job_id, self.project_id, e)

    def _create_aider_coder(self) -> Coder:
        """Create and configure the Aider coder instance."""
        try:
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
        except Exception as e:
            error_msg = f"Failed to create Aider coder: {str(e)}"
            print(f"[code_service] {error_msg}")
            raise AiderError(error_msg, self.job_id, self.project_id, e)

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


def run_with_timeout_and_retries(target, args=(), kwargs={}, max_retries=3, retry_delay=15, timeout=120, job_id=None, project_id=None):
    """Run a target function with timeout handling and retries using multiprocessing."""
    from queue import Empty
    import time

    def target_wrapper(queue, *args, **kwargs):
        try:
            result = target(*args, **kwargs)
            queue.put(('success', result))
        except Exception as e:
            queue.put(('error', e))

    for attempt in range(max_retries):
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=target_wrapper,
            args=(queue,) + args,
            kwargs=kwargs,
            daemon=True
        )

        try:
            process.start()
            process.join(timeout=timeout)

            # Check if process is still running (timeout occurred)
            if process.is_alive():
                print(f"Process still running after {timeout}s timeout, terminating...")
                process.terminate()
                time.sleep(1)  # Give process time to terminate
                if process.is_alive():
                    print("Process still alive after terminate(), using kill()")
                    process.kill()
                process.join(1)  # Wait briefly for resources to clean up

                if attempt < max_retries - 1:
                    print(f"Timeout attempt {attempt+1}/{max_retries}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    if job_id and project_id:
                        print(f"Final timeout for job {job_id}, raising AiderTimeoutError")
                        raise AiderTimeoutError(job_id, project_id, timeout)
                    else:
                        print(f"Final timeout, raising TimeoutError")
                        raise TimeoutError(f"Process timed out after {timeout} seconds")

            # Process completed within timeout, check for result
            try:
                result_type, result_data = queue.get(block=False)
                if result_type == 'success':
                    return result_data
                else:  # result_type == 'error'
                    if attempt < max_retries - 1:
                        print(f"Error: {str(result_data)}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        if job_id and project_id:
                            raise AiderExecutionError(job_id, project_id, result_data)
                        else:
                            raise result_data  # Re-raise the exception on final attempt
            except Empty:
                if attempt < max_retries - 1:
                    print(f"Process completed but returned no result, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    if job_id and project_id:
                        raise AiderExecutionError(job_id, project_id, RuntimeError("Process failed to return any result"))
                    else:
                        raise RuntimeError("Process failed to return any result")

        except AiderTimeoutError:
            raise
        except AiderExecutionError:
            raise
        except Exception as e:
            # Handle any other exceptions that aren't already caught
            if attempt < max_retries - 1:
                print(f"Unexpected error: {str(e)}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            else:
                if job_id and project_id:
                    raise CodeServiceError(f"Unexpected error during execution", job_id, project_id, e)
                else:
                    raise

    # This should never be reached due to the exception handling above
    if job_id and project_id:
        raise CodeServiceError(f"Failed after {max_retries} attempts", job_id, project_id)
    else:
        raise RuntimeError(f"Failed after {max_retries} attempts")


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
