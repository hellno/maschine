import os
import git
import shutil
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
from backend.db import Database
from backend.config.project_config import ProjectConfig

class GitService:
    """Manages Git operations with robust state handling and recovery"""
    
    def __init__(self, repo_path: str, job_id: str, db: Database, enable_backup: bool = False):
        print(f"[GitService] Initializing for repo: {repo_path}, job: {job_id}")
        self.repo_path = repo_path
        self.job_id = job_id
        self.db = db
        self.repo_dir = os.path.join(ProjectConfig.PATHS["GITHUB_REPOS"], repo_path)
        self.repo: Optional[git.Repo] = None
        self.enable_backup = enable_backup
        self.backup_dir = os.path.join(self.repo_dir + "_backup", datetime.now().isoformat()) if enable_backup else None
        print(f"[GitService] Using repo_dir: {self.repo_dir}")
        print(f"[GitService] Backup enabled: {enable_backup}")

    def ensure_repo_ready(self) -> git.Repo:
        """Ensures repository is in a valid, up-to-date state"""
        try:
            print(f"[GitService] Starting ensure_repo_ready for {self.repo_path}")
            if not self._is_valid_repo():
                print(f"[GitService] No valid repo found at {self.repo_dir}, will clone fresh")
                self._clone_fresh()
            else:
                print(f"[GitService] Found existing repo at {self.repo_dir}, validating")
                self._validate_and_repair()
            
            print(f"[GitService] Configuring git user")
            self.repo.git.config('user.name', ProjectConfig.GITHUB["COMMIT_NAME"])
            self.repo.git.config('user.email', ProjectConfig.GITHUB["COMMIT_EMAIL"])
            print(f"[GitService] Repository ready at {self.repo_dir}")
            return self.repo
            
        except Exception as e:
            error_msg = f"Error ensuring repo ready: {str(e)}"
            print(f"[GitService] {error_msg}")
            self.db.add_log(self.job_id, "git", error_msg)
            raise

    def safe_pull(self) -> bool:
        """Safely pull latest changes, handling conflicts"""
        print(f"[GitService] ====== Starting safe_pull ======")
        print(f"[GitService] Repo path: {self.repo_path}")
        print(f"[GitService] Repo dir: {self.repo_dir}")
        try:
            if self.enable_backup:
                print(f"[GitService] Creating backup before pull")
                self._backup_working_tree()
            else:
                print(f"[GitService] Backup disabled, skipping")
            
            print(f"[GitService] Fetching from remote")
            print(f"[GitService] Remote URLs: {[remote.url for remote in self.repo.remotes]}")
            self.repo.remotes.origin.fetch()
            print(f"[GitService] Fetch completed")
            
            if self._has_local_changes():
                print(f"[GitService] Local changes detected, handling them")
                result = self._handle_local_changes()
                print(f"[GitService] Local changes handled with result: {result}")
                return result
            
            print(f"[GitService] No local changes, resetting to origin/main")    
            self.repo.git.reset('--hard', 'origin/main')
            print(f"[GitService] Reset completed")
            self.repo.git.clean('-fd')
            print(f"[GitService] Clean completed")
            print(f"[GitService] Pull completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error during safe pull: {str(e)}"
            print(f"[GitService] {error_msg}")
            print(f"[GitService] Exception type: {type(e)}")
            print(f"[GitService] Exception details: {str(e)}")
            if self.enable_backup:
                print(f"[GitService] Attempting to restore from backup")
                self._restore_from_backup()
            self.db.add_log(self.job_id, "git", error_msg)
            return False
        finally:
            if self.enable_backup:
                print(f"[GitService] Cleaning up backup")
                self._cleanup_backup()
            print(f"[GitService] ====== Completed safe_pull ======")

    def safe_push(self, commit_message: str = "Automated update") -> bool:
        """Safely commit and push changes"""
        print(f"[GitService] ====== Starting safe_push ======")
        print(f"[GitService] Repo path: {self.repo_path}")
        print(f"[GitService] Commit message: {commit_message}")
        try:
            if not self._has_local_changes():
                print(f"[GitService] No local changes to push")
                return True
                
            if self.enable_backup:
                print(f"[GitService] Creating backup before push")
                self._backup_working_tree()
            else:
                print(f"[GitService] Backup disabled, skipping")
            
            print(f"[GitService] Adding all changes")
            self.repo.git.add(A=True)
            print(f"[GitService] Creating commit")
            self.repo.index.commit(commit_message)
            print(f"[GitService] Commit created")
            
            try:
                print(f"[GitService] Pushing to remote")
                print(f"[GitService] Remote URLs: {[remote.url for remote in self.repo.remotes]}")
                self.repo.git.push('origin', 'main')
                print(f"[GitService] Push completed successfully")
                return True
            except git.GitCommandError as e:
                print(f"[GitService] Push error: {str(e)}")
                if "fetch first" in str(e):
                    print(f"[GitService] Push rejected, handling rejection")
                    return self._handle_push_rejection()
                print(f"[GitService] Unhandled push error")
                raise
                
        except Exception as e:
            error_msg = f"Error during safe push: {str(e)}"
            print(f"[GitService] {error_msg}")
            print(f"[GitService] Exception type: {type(e)}")
            print(f"[GitService] Exception details: {str(e)}")
            if self.enable_backup:
                print(f"[GitService] Attempting to restore from backup")
                self._restore_from_backup()
            self.db.add_log(self.job_id, "git", error_msg)
            return False
        finally:
            if self.enable_backup:
                print(f"[GitService] Cleaning up backup")
                self._cleanup_backup()
            print(f"[GitService] ====== Completed safe_push ======")

    def _is_valid_repo(self) -> bool:
        """Check if repo exists and is valid"""
        try:
            if not os.path.exists(self.repo_dir):
                return False
            self.repo = git.Repo(self.repo_dir)
            return bool(self.repo.git_dir)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return False

    def _clone_fresh(self) -> None:
        """Perform fresh clone of repository"""
        try:
            if os.path.exists(self.repo_dir):
                print(f"[GitService] Removing existing directory: {self.repo_dir}")
                shutil.rmtree(self.repo_dir)
                
            print(f"[GitService] Starting clone...")
            print(f"[GitService] Repo path: {self.repo_path}")
            print(f"[GitService] Has GitHub token: {bool(os.environ['GITHUB_TOKEN'])}")
            print(f"[GitService] Clone URL: https://[token]@github.com/{self.repo_path}.git")
            
            clone_url = f"https://{os.environ['GITHUB_TOKEN']}@github.com/{self.repo_path}.git"
            self.repo = git.Repo.clone_from(
                clone_url, 
                self.repo_dir,
                depth=1,
                single_branch=True,
                branch="main"
            )
            
            # Verify repo contents
            print(f"[GitService] Verifying repository contents in: {self.repo_dir}")
            files = os.listdir(self.repo_dir)
            print(f"[GitService] Repository contents: {files}")
            
            if not os.path.exists(os.path.join(self.repo_dir, "package.json")):
                raise Exception(f"package.json not found after clone in {self.repo_dir}")
                
            print(f"[GitService] Fresh clone completed successfully")
            return self.repo
            
        except Exception as e:
            error_msg = f"Clone failed: {str(e)}"
            print(f"[GitService] {error_msg}")
            print(f"[GitService] Exception type: {type(e)}")
            print(f"[GitService] Full exception details: {str(e)}")
            self.db.add_log(self.job_id, "git", error_msg)
            raise

    def _validate_and_repair(self) -> None:
        """Validate repo state and repair if needed"""
        try:
            self.repo = git.Repo(self.repo_dir)
            self.repo.git.status()
        except (git.InvalidGitRepositoryError, git.GitCommandError):
            self._clone_fresh()

    def _has_local_changes(self) -> bool:
        """Check for uncommitted or unpushed changes"""
        return self.repo.is_dirty() or bool(self.repo.untracked_files)

    def _backup_working_tree(self) -> None:
        """Backup current working tree state"""
        if os.path.exists(self.repo_dir):
            os.makedirs(os.path.dirname(self.backup_dir), exist_ok=True)
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            shutil.copytree(self.repo_dir, self.backup_dir, symlinks=True)

    def _restore_from_backup(self) -> None:
        """Restore from backup if available"""
        if os.path.exists(self.backup_dir):
            if os.path.exists(self.repo_dir):
                shutil.rmtree(self.repo_dir)
            shutil.copytree(self.backup_dir, self.repo_dir, symlinks=True)
            self.repo = git.Repo(self.repo_dir)

    def _cleanup_backup(self) -> None:
        """Clean up backup directory"""
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)

    def _handle_local_changes(self) -> bool:
        """Handle local changes during pull"""
        try:
            # Try stash-pull-pop approach first
            self.repo.git.stash()
            self.repo.git.pull('origin', 'main')
            try:
                self.repo.git.stash('pop')
                return True
            except git.GitCommandError:
                # Conflict during pop, take remote version
                self.repo.git.reset('--hard', 'origin/main')
                self.repo.git.clean('-fd')
                return True
        except git.GitCommandError:
            # If stash fails, force reset to remote
            self.repo.git.reset('--hard', 'origin/main')
            self.repo.git.clean('-fd')
            return True

    def _handle_push_rejection(self) -> bool:
        """Handle push rejection due to remote changes"""
        try:
            current_changes = self.repo.git.diff('HEAD')
            self.repo.git.fetch()
            self.repo.git.reset('--hard', 'origin/main')
            
            if current_changes:
                # Apply our changes on top of latest remote
                self.repo.git.apply('--3way', input=current_changes)
                self.repo.git.add(A=True)
                self.repo.index.commit("Reapplied changes on top of remote")
                self.repo.git.push('origin', 'main')
            return True
            
        except git.GitCommandError:
            # If reapply fails, take remote version
            self.repo.git.reset('--hard', 'origin/main')
            self.repo.git.clean('-fd')
            return False
