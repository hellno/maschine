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
from backend.utils.package_commands import handle_package_install_commands, parse_sandbox_process
from backend.services.build_runner import BuildRunner
from backend.exceptions import (
    CodeServiceError, SandboxError, SandboxCreationError, SandboxTerminationError,
    GitError, GitCloneError, GitPushError,
    BuildError, InstallError, CompileError,
    AiderError, AiderTimeoutError, AiderExecutionError
)





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
        """Run the Aider coder with the given prompt.
        
        Orchestrates the full process of code generation, building, and deployment:
        1. Validates setup and initializes logging
        2. Runs Aider code generation with context enhancement if requested
        3. Installs any packages mentioned in Aider output
        4. Builds the project and attempts to fix any build errors
        5. Syncs changes to Git and triggers a deployment build
        
        Args:
            prompt: The user prompt to process
            auto_enhance_context: Whether to automatically enhance the prompt with context
            
        Returns:
            Dictionary with status and build logs
            
        Raises:
            Various custom exceptions for different error conditions
        """
        try:
            # Initial validation and setup
            self._validate_setup()
            self._log_start(prompt)
            
            # Run Aider to generate code changes
            aider_result = self._run_aider_process(prompt, auto_enhance_context)
            
            # Process any package installations from Aider output
            self._handle_package_installs(aider_result)
            
            # Run initial build to check for errors
            build_success = self._execute_build()
            
            # If build failed, attempt to fix errors
            if not build_success:
                fixed = self._attempt_build_error_fix(aider_result)
                if not fixed:
                    self.db.add_log(self.job_id, "build", "Failed to fix build errors after multiple attempts")
            
            # Finalize changes and trigger deployment
            self._finalize_successful_run()
            
            # Complete job and return success response
            return self._build_success_response()
            
        except (AiderTimeoutError, AiderExecutionError) as e:
            return self._handle_known_error(e)
        except (InstallError, CompileError, BuildError) as e:
            return self._handle_known_error(e)
        except GitError as e:
            return self._handle_known_error(e)
        except SandboxError as e:
            return self._handle_known_error(e)
        except Exception as e:
            return self._handle_unexpected_error(e)

    def _validate_setup(self):
        """Ensure required components are initialized."""
        if not self.db or not self.is_setup:
            raise CodeServiceError(
                "Service not properly initialized",
                self.job_id,
                self.project_id
            )

    def _log_start(self, prompt: str):
        """Log initial process startup."""
        self.db.update_job_status(self.job_id, "running")
        self.db.add_log(self.job_id, "system", f"Starting code generation with prompt: {prompt[:200]}...")
        print(f"[code_service] Starting code generation with prompt: {prompt[:200]}...")

    def _run_aider_process(self, prompt: str, enhance_context: bool) -> str:
        """Execute Aider with enhanced context and retries."""
        self.db.add_log(self.job_id, "aider", "Starting code generation")
        
        try:
            aider_runner = AiderRunner(
                job_id=self.job_id,
                project_id=self.project_id,
                user_context=self.user_context
            )
            coder = self._create_aider_coder()
            
            if enhance_context:
                prompt = aider_runner.enhance_prompt_with_context(prompt)
                self.db.add_log(self.job_id, "aider", "Enhanced prompt with context")

            print(f"[code_service] Running Aider with prompt: {prompt}")
            result = aider_runner.run_aider(coder, prompt)
            self.db.add_log(self.job_id, "aider", f"Completed code generation, generated {len(result)} characters")
            print(f"[code_service] Aider result (truncated): {result[:250]}")
            return result
        
        except AiderTimeoutError as e:
            self.db.add_log(self.job_id, "aider", f"Timeout after {e.timeout}s")
            raise
        except AiderExecutionError as e:
            self.db.add_log(self.job_id, "aider", f"Execution failed: {str(e.original_exception)}")
            raise

    def _handle_package_installs(self, aider_result: str):
        """Process package installation commands from Aider output."""
        self.db.add_log(self.job_id, "system", "Checking for package installs")
        print("[code_service] Checking for package install commands")
        try:
            handle_package_install_commands(
                aider_result,
                self.sandbox,
                parse_sandbox_process
            )
            self.db.add_log(self.job_id, "system", "Package installation completed")
            print("[code_service] Package installation completed")
        except Exception as e:
            error_msg = f"Package installation failed: {str(e)}"
            self.db.add_log(self.job_id, "system", error_msg)
            print(f"[code_service] {error_msg}")
            raise InstallError(self.job_id, self.project_id, e)

    def _execute_build(self) -> bool:
        """Run build process and return success status."""
        self.db.add_log(self.job_id, "build", "Starting initial build")
        print("[code_service] Starting initial build")
        try:
            has_errors, logs = self._run_build_in_sandbox()
            
            if has_errors:
                error_msg = f"Build failed with errors: {logs[:500]}..."
                self.db.add_log(self.job_id, "build", error_msg)
                print(f"[code_service] {error_msg}")
                return False
            
            self.db.add_log(self.job_id, "build", "Build completed successfully")
            print("[code_service] Build completed successfully")
            return True
        except (InstallError, CompileError) as e:
            error_msg = f"Build error: {str(e)}"
            self.db.add_log(self.job_id, "build", error_msg)
            print(f"[code_service] {error_msg}")
            return False

    def _attempt_build_error_fix(self, aider_result: str) -> bool:
        """Attempt to fix build errors using Aider."""
        self.db.add_log(self.job_id, "system", "Attempting to fix build errors")
        print("[code_service] Attempting to fix build errors")
        
        try:
            logs = self._get_build_logs()
            
            aider_runner = AiderRunner(
                job_id=self.job_id,
                project_id=self.project_id,
                user_context=self.user_context
            )
            
            fix_prompt = aider_runner.generate_fix_for_errors(logs)
            self.db.add_log(self.job_id, "aider", "Generated error fix prompt")
            print("[code_service] Generated error fix prompt and running Aider again")
            
            coder = self._create_aider_coder()
            fix_result = aider_runner.run_aider(coder, fix_prompt)
            
            if fix_result:
                self.db.add_log(self.job_id, "aider", f"Generated fix, length: {len(fix_result)}")
                print(f"[code_service] Fix attempt result (truncated): {fix_result[:250]}")
                
                # Process any package installations from fix
                self._handle_package_installs(fix_result)
                
            # Run build again to see if errors were fixed
            has_errors, logs = self._run_build_in_sandbox(terminate_after_build=True)
            
            if has_errors:
                self.db.add_log(self.job_id, "build", "Build errors persist after fix attempt")
                print("[code_service] Build errors persist after fix attempt")
                return False
                
            self.db.add_log(self.job_id, "build", "Build errors successfully fixed")
            print("[code_service] Build errors successfully fixed")
            return True
            
        except AiderError as e:
            error_msg = f"Fix attempt failed: {str(e)}"
            self.db.add_log(self.job_id, "system", error_msg)
            print(f"[code_service] {error_msg}")
            return False

    def _finalize_successful_run(self):
        """Handle successful execution flow."""
        self.db.add_log(self.job_id, "system", "Finalizing successful run")
        print("[code_service] Finalizing successful run")
        
        try:
            # Sync changes to git repository
            self.db.add_log(self.job_id, "git", "Syncing code changes to git repository")
            print("[code_service] Syncing code changes to git repository")
            self._sync_git_changes()
            
            # Create build and start async polling
            self.db.add_log(self.job_id, "system", "Creating build and starting deployment")
            print("[code_service] Creating build and starting deployment")
            self._create_build_and_poll_status_async()
            
        except GitError as e:
            error_msg = f"Final git sync failed: {str(e)}"
            self.db.add_log(self.job_id, "git", error_msg)
            print(f"[code_service] {error_msg}")
            raise

    def _build_success_response(self) -> dict:
        """Generate final success response."""
        self.db.update_job_status(self.job_id, "completed")
        self.db.add_log(self.job_id, "system", "Code service process completed successfully")
        print("[code_service] Code service process completed successfully")
        
        return {
            "status": "success",
            "message": "Code generation and build completed successfully"
        }

    def _handle_known_error(self, error: Exception) -> dict:
        """Handle expected error types with proper logging."""
        error_type = type(error).__name__
        error_msg = f"{error_type}: {str(error)}"
        
        print(f"[code_service] {error_msg}")
        category = "error"
        
        if isinstance(error, AiderError):
            category = "aider"
        elif isinstance(error, BuildError):
            category = "build"
        elif isinstance(error, GitError):
            category = "git"
        elif isinstance(error, SandboxError):
            category = "sandbox"
            
        self.db.add_log(self.job_id, category, error_msg)
        self.db.update_job_status(self.job_id, "failed", error_msg)
        self.terminate_sandbox()
        
        # Return error information instead of raising
        return {
            "status": "error",
            "error_type": error_type,
            "message": error_msg
        }
        
    def _handle_unexpected_error(self, error: Exception) -> dict:
        """Fallback handler for unexpected exceptions."""
        error_msg = f"Unexpected error during code generation: {str(error)}"
        print(f"[code_service] {error_msg}")
        self.db.add_log(self.job_id, "backend", error_msg)
        self.db.update_job_status(self.job_id, "failed", error_msg)
        self.terminate_sandbox()
        
        # Return error information instead of raising
        return {
            "status": "error",
            "error_type": "UnexpectedError",
            "message": error_msg
        }

    def _get_build_logs(self) -> str:
        """Retrieve and format build logs for error analysis."""
        build = self.db.get_latest_build(self.project_id)
        if not build:
            return "No build logs available"
        return build.get("data", {}).get("logs", "No logs available")

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
