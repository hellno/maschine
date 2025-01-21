import os
import git
import shutil
from typing import Optional, Tuple, List
import time  # Moved to top level
from pathlib import Path
from datetime import datetime
from backend.db import Database
from backend.config.project_config import ProjectConfig
from backend.services.project_volume import ProjectVolume

class GitService:
    """Manages Git operations with robust state handling and recovery"""
    
    def __init__(self, project_id: str, job_id: str, db: Database, enable_backup: bool = False):
        print(f"[GitService] Initializing for project: {project_id}, job: {job_id}")
        self.project_id = project_id
        self.job_id = job_id
        self.db = db
        self.volume = ProjectVolume(project_id)
        self.repo_dir = self.volume.paths["repo"]
        self.repo: Optional[git.Repo] = None
        self.enable_backup = enable_backup
        self.backup_dir = os.path.join(self.repo_dir + "_backup", datetime.now().isoformat()) if enable_backup else None
        print(f"[GitService] Using repo_dir: {self.repo_dir}")
        print(f"[GitService] Backup enabled: {enable_backup}")

    def is_repo_in_use(self) -> bool:
        """Check if repo has a lock file indicating it's being modified"""
        if not os.path.exists(self.repo_dir):
            return False  # If directory doesn't exist, it can't be in use
            
        lock_file = os.path.join(self.repo_dir, '.update-in-progress')
        if not os.path.exists(lock_file):
            return False
            
        # Check if lock is stale (older than 30 minutes)
        try:
            with open(lock_file, 'r') as f:
                timestamp = datetime.fromisoformat(f.read().strip())
            if (datetime.now() - timestamp).total_seconds() > 1800:  # 30 minutes
                print(f"[GitService] Removing stale lock file from {timestamp}")
                os.remove(lock_file)  # Clean up stale lock
                return False
        except Exception as e:
            print(f"[GitService] Invalid lock file, ignoring: {e}")
            return False  # If we can't read timestamp, assume lock is invalid
            
        return True

    def mark_repo_in_use(self):
        """Create lock file atomically"""
        import tempfile
        import shutil
        
        # Ensure parent directory exists
        os.makedirs(self.repo_dir, exist_ok=True)
        
        lock_file = os.path.join(self.repo_dir, '.update-in-progress')
        temp_file = None
        try:
            # Create temp file with timestamp
            fd, temp_file = tempfile.mkstemp(dir=os.path.dirname(self.repo_dir))
            with os.fdopen(fd, 'w') as f:
                f.write(str(datetime.now()))
            
            # Atomic move
            shutil.move(temp_file, lock_file)
            print(f"[GitService] Created lock file: {lock_file}")
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            print(f"[GitService] Warning: Failed to create lock file: {e}")
            # Don't raise the exception - if we can't create the lock file,
            # we should still try to proceed with the update

    def clear_repo_in_use(self):
        """Remove lock file after modifications complete"""
        lock_file = os.path.join(self.repo_dir, '.update-in-progress')
        if os.path.exists(lock_file):
            os.remove(lock_file)
            
    def _count_inodes(self, path: str) -> int:
        """Count total number of inodes (files + directories) in a path"""
        total = 0
        for root, dirs, files in os.walk(path):
            total += len(dirs) + len(files) + 1  # +1 for root dir itself
        return total

    def _get_repo_stats(self) -> List[Tuple[str, float, int]]:
        """Get list of repos with their last access time and inode count"""
        stats = []
        volume_root = ProjectConfig.PATHS["GITHUB_REPOS"]
        if not os.path.exists(volume_root):
            return stats
            
        for item in os.listdir(volume_root):
            item_path = os.path.join(volume_root, item)
            if os.path.isdir(item_path):
                try:
                    # Skip if it's not a git repo
                    if not os.path.exists(os.path.join(item_path, '.git')):
                        continue
                        
                    last_access = os.path.getatime(item_path)
                    inode_count = self._count_inodes(item_path)
                    stats.append((item_path, last_access, inode_count))
                except Exception as e:
                    print(f"[GitService] Warning: Error getting stats for {item_path}: {e}")
                    continue
        
        # Sort by last access time (newest first)
        return sorted(stats, key=lambda x: x[1], reverse=True)

    def cleanup_old_repos(self):
        """Clean up repos that haven't been accessed in a while"""
        try:
            if not os.path.exists(self.repo_dir):
                return
                
            print(f"[GitService] Starting cleanup of old repos in {self.repo_dir}")
            repo_stats = self._get_repo_stats()
            
            if not repo_stats:
                print("[GitService] No repositories found")
                return
                
            total_inodes = sum(stats[2] for stats in repo_stats)
            print(f"[GitService] Total inodes in use: {total_inodes}")
            
            # Keep only the 5 most recently accessed repos
            repos_to_remove = repo_stats[5:]
            
            for repo_path, last_access, inode_count in repos_to_remove:
                try:
                    print(f"[GitService] Removing {repo_path} (inodes: {inode_count}, last accessed: {datetime.fromtimestamp(last_access)})")
                    shutil.rmtree(repo_path)
                    self.db.add_log(self.job_id, "cleanup", f"Removed old repository: {repo_path}")
                except Exception as e:
                    print(f"[GitService] Warning: Error cleaning up {repo_path}: {e}")
                    continue
                    
            # Get final inode count
            remaining_stats = self._get_repo_stats()
            remaining_inodes = sum(stats[2] for stats in remaining_stats)
            print(f"[GitService] Cleanup complete. Remaining inodes: {remaining_inodes}")
                
        except Exception as e:
            print(f"[GitService] Warning: Cleanup error: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up resources and file handles"""
        try:
            # Change to safe directory first
            print(f"[GitService] Starting cleanup from: {os.getcwd()}")
            os.chdir('/tmp')
            print(f"[GitService] Changed to safe directory: {os.getcwd()}")
            
            if self.repo:
                print(f"[GitService] Cleaning up repo resources")
                try:
                    # Close all git objects and references
                    for submodule in self.repo.submodules:
                        submodule.remove()
                    
                    # Close all remote references
                    for remote in self.repo.remotes:
                        remote.remove(self.repo, remote.name)
                    
                    # Force close the repo
                    self.repo.close()
                    
                    # Clear git object cache if it exists
                    pack_dir = os.path.join(self.repo_dir, '.git', 'objects', 'pack')
                    if os.path.exists(pack_dir):
                        print(f"[GitService] Cleaning pack directory: {pack_dir}")
                        git.util.rmtree(pack_dir)
                        os.makedirs(pack_dir, exist_ok=True)
                except Exception as e:
                    print(f"[GitService] Warning: Error closing repo: {e}")
                
                # Clear the repo reference
                self.repo = None
                
            # Force garbage collection
            import gc
            gc.collect()
            
            # Force sync filesystem and commit volume
            os.sync()
            from modal_app import github_repos
            github_repos.commit()
            time.sleep(0.5)
            
            print(f"[GitService] Cleanup completed")
            
        except Exception as e:
            print(f"[GitService] Cleanup warning: {e}")

    def _ensure_clean_state(self):
        """Ensure clean state for volume operations"""
        self._cleanup_resources()
        
        # Store original working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to a safe directory outside the volume
            os.chdir('/tmp')
            print(f"[GitService] Changed to safe directory: {os.getcwd()}")
            
            # Get volume reference and ensure clean state
            from modal_app import github_repos
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Close any open files and handles
                    import gc
                    gc.collect()  # Force garbage collection to close file handles
                    
                    # Force close git pack files
                    if self.repo:
                        # Close all git objects and references
                        for submodule in self.repo.submodules:
                            submodule.remove()
                        for remote in self.repo.remotes:
                            remote.remove(self.repo, remote.name)
                        self.repo.close()
                        self.repo = None
                    
                    # Force sync filesystem and commit volume
                    os.sync()
                    github_repos.commit()
                    time.sleep(1)  # Give OS time to close handles
                    
                    # Attempt to reload the volume
                    print(f"[GitService] Attempting volume reload...")
                    github_repos.reload()
                    print(f"[GitService] Volume reload successful")
                    break
                except Exception as e:
                    error_msg = str(e)
                    print(f"[GitService] Reload attempt {attempt + 1} failed: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        print(f"[GitService] Waiting before retry...")
                        time.sleep(2 * (attempt + 1))  # Use time from top import
                        self._cleanup_resources()
                    else:
                        print(f"[GitService] All reload attempts failed")
                        raise
        finally:
            # Always restore the original working directory
            try:
                os.chdir(original_cwd)
                print(f"[GitService] Restored working directory: {os.getcwd()}")
            except Exception as e:
                print(f"[GitService] Warning: Failed to restore working directory: {e}")

    def ensure_repo_ready(self) -> git.Repo:
        """Ensures repository is in a valid, up-to-date state"""
        try:
            print(f"[GitService] Starting ensure_repo_ready for {self.repo_path}")
            self._ensure_clean_state()
            
            # Always do fresh clone
            print(f"[GitService] Starting fresh clone")
            if os.path.exists(self.repo_dir):
                print(f"[GitService] Removing existing directory: {self.repo_dir}")
                shutil.rmtree(self.repo_dir)
            
            self._clone_fresh()
            
            if not self.repo:
                raise Exception("Failed to initialize repository")
                
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
            # Ensure repo is initialized
            if not self.repo:
                print(f"[GitService] Repository not initialized, attempting to initialize...")
                self.ensure_repo_ready()
                
            if not self.repo:
                raise Exception("Failed to initialize repository")

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
            
            # Get list of changed files before commit
            changed_files = self.repo.git.diff('--cached', '--name-only').splitlines()
            print(f"[GitService] Files to be committed: {changed_files}")
            
            # Create commit and get commit object
            print(f"[GitService] Creating commit with message: {commit_message}")
            commit = self.repo.index.commit(commit_message)
            print(f"[GitService] Commit created: {commit.hexsha}")
            print(f"[GitService] Commit stats - files: {len(commit.stats.files)}, insertions: {commit.stats.total['insertions']}, deletions: {commit.stats.total['deletions']}")
            
            try:
                print(f"[GitService] Pushing to remote")
                print(f"[GitService] Remote URLs: {[remote.url for remote in self.repo.remotes]}")
                print(f"[GitService] Current branch: {self.repo.active_branch.name}")
                print(f"[GitService] Local HEAD: {self.repo.head.commit.hexsha}")
                print(f"[GitService] Remote HEAD before push: {self.repo.remotes.origin.refs.main.commit.hexsha}")
                
                self.repo.git.push('origin', 'main')
                
                # Fetch to update remote refs
                self.repo.remotes.origin.fetch()
                print(f"[GitService] Remote HEAD after push: {self.repo.remotes.origin.refs.main.commit.hexsha}")
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
        if not self.repo:
            raise Exception("Repository not initialized")
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
