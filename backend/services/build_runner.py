import os
import time
import modal
from typing import Dict, List, Tuple, Optional
from backend.integrations.db import Database
from backend.exceptions import (
    BuildError, InstallError, CompileError,
    VercelBuildError, VercelAPIError
)
from backend.utils.package_commands import parse_sandbox_process
from backend import config

class BuildRunner:
    """Orchestrates build execution, error analysis, and status tracking"""
    
    def __init__(self, project_id: str, db: Database, job_id: Optional[str] = None):
        self.project_id = project_id
        self.db = db
        self.job_id = job_id
        
    def run_build_in_sandbox(self, sandbox, terminate_after_build: bool = False) -> Tuple[bool, str]:
        """Run build commands in a sandbox and return results"""
        try:
            logs = []
            
            # Check git status
            has_new_commits, has_pending_changes = self._get_git_repo_status(sandbox)
            if not has_new_commits and not has_pending_changes:
                print("[build] No new commits or pending changes. skipping to build again")
                return False, "No new commits or pending changes"
                
            # Get git log
            git_log = sandbox.exec("git", "log", "-1", "--oneline")
            log_lines, _ = parse_sandbox_process(git_log)
            logs.extend(log_lines)
            print("[build] Latest commit:", log_lines)
            
            # Run installation
            install_process = sandbox.exec("pnpm", "install")
            install_logs, install_code = parse_sandbox_process(install_process)
            logs.extend(install_logs)
            
            if install_code != 0:
                logs_str = "\n".join(self._clean_log_lines(logs))
                raise InstallError(self.job_id, self.project_id, Exception(f"Install failed with code {install_code}: {logs_str}"))
                
            # Run build
            print("[build] Running build command")
            build_process = sandbox.exec("pnpm", "build")
            build_logs, build_returncode = parse_sandbox_process(build_process)
            logs.extend(build_logs)
            
            # Check for errors
            has_error_in_logs = build_returncode == 1 or any(
                "error" in line.lower()
                or "failed" in line.lower()
                or "exited with 1" in line.lower()
                for line in logs
            )
            
            logs_cleaned = self._clean_log_lines(logs)
            logs_str = "\n".join(logs_cleaned)
            
            if has_error_in_logs and build_returncode != 0:
                raise CompileError(self.job_id, self.project_id, logs_str)
                
            return has_error_in_logs, logs_str
            
        except (CompileError, InstallError):
            # Re-raise these specialized exceptions
            raise
        except Exception as e:
            error_msg = f"Build failed: {str(e)}"
            if self.job_id:
                self.db.add_log(self.job_id, "build", error_msg)
                self.db.update_job_status(self.job_id, "failed", error_msg)
            raise BuildError(self.job_id, self.project_id, e)
            
    def generate_error_fix_prompt(self, logs: str) -> str:
        """Generate a prompt for the AI to fix build errors based on logs"""
        return f"""
    The previous changes caused build errors. Please fix them.
    Here are the build logs showing the errors:

    {logs}

    Please analyze these errors and make the necessary corrections to fix the build.
    """
    
    def start_build_polling(self, build_id: str, commit_hash: str):
        """Start asynchronous polling for build status"""
        try:
            print(f"[build_runner] Starting build polling for build {build_id}")
            # Start an asynchronous function to poll the build status
            poll_build_status_spawn = modal.Function.from_name(
                config.APP_NAME, 
                f"{config.MODAL_POLL_BUILD_FUNCTION_NAME}_spawn"
            )
            poll_build_status_spawn.spawn(
                project_id=self.project_id, 
                build_id=build_id, 
                commit_hash=commit_hash
            )
            print(f"[build_runner] Build polling started for {build_id} with commit {commit_hash}")

        except Exception as e:
            error_msg = f"Failed to start build polling: {str(e)}"
            print(f"[build_runner] {error_msg}")
            if self.job_id:
                self.db.add_log(self.job_id, "backend", error_msg)
                
    def _get_git_repo_status(self, sandbox) -> Tuple[bool, bool]:
        """Get git repo status to check for commits and changes"""
        if not sandbox:
            print('error getting git repo status, sandbox not initialized')
            return False, False

        git_status = sandbox.exec("git", "status")
        status_logs, _ = parse_sandbox_process(git_status)
        print("[build] Current git status:", status_logs)
        no_new_commits = 'Your branch is up to date'
        no_pending_changes = 'nothing to commit'
        has_new_commits = no_new_commits not in "\n".join(status_logs)
        has_pending_changes = no_pending_changes not in "\n".join(status_logs)

        return has_new_commits, has_pending_changes
        
    def _clean_log_lines(self, logs: List[str]) -> List[str]:
        """Clean up log lines for display"""
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
