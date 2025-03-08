import os
import modal
import time
import requests
from typing import Optional, Tuple
import git
from aider.coders import Coder
import tempfile

from backend import config
from backend.modal import base_image
from backend.integrations.db import Database
from backend.integrations.github_api import (
    clone_repo_url_to_dir,
    configure_git_user_for_repo,
)

from backend.types import UserContext
from backend.services.aider_runner import AiderRunner
from backend.utils.package_commands import handle_package_install_commands
from backend.services.build_runner import BuildRunner
from backend.exceptions import (
    CodeServiceError, SandboxError, SandboxCreationError, SandboxTerminationError,
    GitError, GitCloneError, GitPushError,
    BuildError, InstallError, CompileError,
    AiderTimeoutError, AiderExecutionError
)


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
            aider_runner = AiderRunner(
                job_id=self.job_id,
                project_id=self.project_id,
                user_context=self.user_context
            )
            coder = self._create_aider_coder()

            print(f"[code_service] Running Aider with prompt: {prompt}")
            self.db.update_job_status(self.job_id, "running")

            if auto_enhance_context:
                prompt = aider_runner.enhance_prompt_with_context(prompt)

            # Using AiderRunner to handle retries and timeouts
            aider_result = aider_runner.run_aider(coder, prompt)
            handle_package_install_commands(
                aider_result,
                self.sandbox,
                parse_sandbox_process
            )
            print(f"[code_service] Aider result (truncated): {aider_result[:250]}")


            has_errors, logs = self._run_build_in_sandbox()

            if has_errors:
                build_runner = BuildRunner(self.project_id, self.db, self.job_id)
                aider_runner = AiderRunner(
                    job_id=self.job_id,
                    project_id=self.project_id,
                    user_context=self.user_context
                )
                error_fix_prompt = aider_runner.generate_fix_for_errors(logs)
                print("[code_service] Running Aider again to fix build errors")

                aider_result = aider_runner.run_aider(coder, error_fix_prompt)
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

    # Context enhancement now handled by AiderRunner

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

        build_runner = BuildRunner(self.project_id, self.db, self.job_id)
        return build_runner._get_git_repo_status(self.sandbox)

    def _run_build_in_sandbox(
        self, terminate_after_build: bool = False
    ) -> Tuple[bool, str]:
        """Run build commands in an isolated Modal sandbox."""
        try:
            self._create_sandbox(repo_dir=self.repo_dir)

            build_runner = BuildRunner(self.project_id, self.db, self.job_id)
            has_error_in_logs, logs_str = build_runner.run_build_in_sandbox(self.sandbox)

            print(f'terminate_after_build {terminate_after_build} manual_sandbox_termination {self.manual_sandbox_termination}')
            if terminate_after_build and not self.manual_sandbox_termination:
                print("[code_service] Terminating sandbox after build")
                self.terminate_sandbox()

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
        aider_runner = AiderRunner(
            job_id=self.job_id,
            project_id=self.project_id,
            user_context=self.user_context
        )
        return aider_runner.create_aider_coder(self.repo_dir)

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

        build_runner = BuildRunner(self.project_id, self.db, self.job_id)
        build_runner.start_build_polling(build_id, commit_hash)


# Timeout and retry handling moved to AiderRunner class
