import os
import tempfile
import shutil
import time
from typing import Optional, Tuple, List
from modal.container_process import ContainerProcess
from modal import Sandbox
from backend.integrations.db import Database


class SandboxCommandExecutor:
    """
    Executes commands in Modal sandbox with proper logging.
    Made callable to work as a test command for Aider.
    """

    def __init__(self, sandbox: Sandbox, job_id: str, db: Database, repo_dir: str):
        self.sandbox = sandbox
        self.job_id = job_id
        self.db = db
        self.source_dir = repo_dir  # Original repo directory in volume
        self._cmd_str = "pnpm build"
        # Create temp directory that will last for instance lifetime
        self.temp_base = tempfile.mkdtemp(prefix='sandbox_work_')
        self.workdir = os.path.join(self.temp_base, "repo")
        self._setup_workdir()

    def _setup_workdir(self):
        """Setup working directory outside volume"""
        try:
            # Copy repo contents to temp dir
            if os.path.exists(self.workdir):
                shutil.rmtree(self.workdir)
            shutil.copytree(self.source_dir, self.workdir)
            print(f"[SandboxCommandExecutor] Copied repo to temp dir: {self.workdir}")
        except Exception as e:
            print(f"[SandboxCommandExecutor] Error setting up workdir: {e}")
            raise

    def _sync_back_to_volume(self):
        """Sync changes back to volume with proper git handling"""
        try:
            if not os.path.exists(self.workdir):
                return
                
            print(f"[SandboxCommandExecutor] Starting sync to volume")
            
            # Clean up git handles in both directories
            temp_git_dir = os.path.join(self.workdir, '.git')
            vol_git_dir = os.path.join(self.source_dir, '.git')
            
            self._cleanup_git_handles(temp_git_dir)
            self._cleanup_git_handles(vol_git_dir)
            
            # Sync non-git files first
            for item in os.listdir(self.workdir):
                if item not in ['.git', 'node_modules']:
                    src = os.path.join(self.workdir, item)
                    dst = os.path.join(self.source_dir, item)
                    print(f"[SandboxCommandExecutor] Syncing: {item}")
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # Now handle .git directory specially
            if os.path.exists(temp_git_dir):
                print(f"[SandboxCommandExecutor] Syncing git directory")
                if os.path.exists(vol_git_dir):
                    shutil.rmtree(vol_git_dir)
                # Copy git dir without pack files first
                os.makedirs(vol_git_dir)
                for item in os.listdir(temp_git_dir):
                    src = os.path.join(temp_git_dir, item)
                    dst = os.path.join(vol_git_dir, item)
                    if item != 'objects':
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                
                # Handle objects directory specially
                objects_src = os.path.join(temp_git_dir, 'objects')
                objects_dst = os.path.join(vol_git_dir, 'objects')
                if os.path.exists(objects_src):
                    os.makedirs(objects_dst)
                    for item in os.listdir(objects_src):
                        if item != 'pack':  # Skip pack directory initially
                            src = os.path.join(objects_src, item)
                            dst = os.path.join(objects_dst, item)
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)
                    
                    # Finally, handle pack directory with extra care
                    pack_src = os.path.join(objects_src, 'pack')
                    pack_dst = os.path.join(objects_dst, 'pack')
                    if os.path.exists(pack_src):
                        os.makedirs(pack_dst)
                        # Force close any handles again before final copy
                        self._cleanup_git_handles(temp_git_dir)
                        time.sleep(0.5)  # Small delay to ensure handles are released
                        # Copy pack files
                        for item in os.listdir(pack_src):
                            src = os.path.join(pack_src, item)
                            dst = os.path.join(pack_dst, item)
                            shutil.copy2(src, dst)
            
            print(f"[SandboxCommandExecutor] Sync complete")
            
        except Exception as e:
            print(f"[SandboxCommandExecutor] Error during sync: {e}")
            raise

    def execute(self, command: str, capture_output: bool = True) -> Tuple[int, List[str]]:
        """Execute command in sandbox using temp directory outside volume"""
        original_cwd = os.getcwd()
        print(f"[SandboxCommandExecutor] Original working directory: {original_cwd}")
        
        try:
            os.chdir(self.workdir)
            print(f"[SandboxCommandExecutor] Changed to working directory: {os.getcwd()}")
            print(f"[SandboxCommandExecutor] Running command: {command}")
            print(f"[SandboxCommandExecutor] Using workdir: {self.workdir}")

            # Split command string into list of arguments
            command_args = command.split() if isinstance(command, str) else command
            
            process = self.sandbox.exec(
                *command_args,
                workdir=self.workdir  # Use temp dir instead of volume
            )

            output = []
            if capture_output:
                # Capture stdout
                for line in process.stdout:
                    line_str = line.strip()
                    output.append(line_str)
                    print(f"[STDOUT] {line_str}")
                    if self.db and self.job_id:
                        self.db.add_log(self.job_id, "sandbox", line_str)

                # Capture stderr
                for line in process.stderr:
                    line_str = line.strip()
                    output.append(f"ERROR: {line_str}")
                    print(f"[STDERR] {line_str}")
                    if self.db and self.job_id:
                        self.db.add_log(self.job_id, "sandbox", f"ERROR: {line_str}")

            exit_code = process.wait()
            print(f"[SandboxCommandExecutor] Command completed with exit code: {exit_code}")
            print(f"[SandboxCommandExecutor] Changes before sync: {[f for f in os.listdir(self.workdir) if os.path.isfile(os.path.join(self.workdir, f))]}")

            # Sync changes back to volume after successful command
            if exit_code == 0:
                self._sync_back_to_volume()
                print(f"[SandboxCommandExecutor] Changes after sync: {[f for f in os.listdir(self.source_dir) if os.path.isfile(os.path.join(self.source_dir, f))]}")

            return exit_code, output

        except Exception as e:
            error_msg = f"Error executing command '{command}': {str(e)}"
            print(f"[SandboxCommandExecutor] {error_msg}")
            if self.db and self.job_id:
                self.db.add_log(self.job_id, "sandbox", error_msg)
            return 1, [error_msg]

    def __call__(self, cmd: str = None) -> Optional[str]:
        """Makes class callable as required by Aider's test command interface"""
        try:
            cmd_to_run = cmd or self._cmd_str
            exit_code, output = self.execute(cmd_to_run)
            return None  # Always return None to let Aider continue
        except Exception as e:
            print(f"[SandboxCommandExecutor] Error: {e}")
            return None

    def __str__(self) -> str:
        """String representation for Aider's logging"""
        return self._cmd_str

    def __add__(self, other: str) -> str:
        """Support string concatenation"""
        return str(self) + other

    def __radd__(self, other: str) -> str:
        """Support string concatenation from the left"""
        return other + str(self)

    def _cleanup_git_handles(self, git_dir: str):
        """Explicitly cleanup git handles and pack files"""
        try:
            print(f"[SandboxCommandExecutor] Cleaning up git handles in: {git_dir}")
            if not os.path.exists(git_dir):
                return

            # Force close any git pack files
            pack_dir = os.path.join(git_dir, 'objects', 'pack')
            if os.path.exists(pack_dir):
                print(f"[SandboxCommandExecutor] Found pack directory: {pack_dir}")
                # Force sync to ensure writes are complete
                os.sync()
                
                # List pack files before cleanup
                pack_files = [f for f in os.listdir(pack_dir) if f.endswith('.pack')]
                print(f"[SandboxCommandExecutor] Pack files before cleanup: {pack_files}")
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Small delay to allow OS to release handles
                time.sleep(0.5)
                
                # Verify pack files are closed
                try:
                    for pack_file in pack_files:
                        pack_path = os.path.join(pack_dir, pack_file)
                        # Try to open and close file to check if it's locked
                        with open(pack_path, 'rb'):
                            pass
                    print(f"[SandboxCommandExecutor] All pack files are closed")
                except Exception as e:
                    print(f"[SandboxCommandExecutor] Warning: Some pack files may still be open: {e}")
                    
        except Exception as e:
            print(f"[SandboxCommandExecutor] Warning during git cleanup: {e}")

    def cleanup(self):
        """Cleanup with proper handle closing"""
        try:
            if os.path.exists(self.workdir):
                print(f"[SandboxCommandExecutor] Starting cleanup")
                # Clean up git handles first
                git_dir = os.path.join(self.workdir, '.git')
                self._cleanup_git_handles(git_dir)
                
                # Force change directory out of temp dir
                os.chdir('/tmp')
                
                # Force sync and small delay
                os.sync()
                time.sleep(0.5)
                
                # Now remove the directory
                shutil.rmtree(self.temp_base)
                print(f"[SandboxCommandExecutor] Cleanup complete")
        except Exception as e:
            print(f"[SandboxCommandExecutor] Error during cleanup: {e}")
