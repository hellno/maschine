from typing import Optional, Tuple, List
from modal.container_process import ContainerProcess
from modal import Sandbox
from backend.db import Database

class SandboxCommandExecutor:
    """
    Executes commands in Modal sandbox with proper logging.
    Made callable to work as a test command for Aider.
    """
    
    def __init__(self, sandbox: Sandbox, job_id: str, db: Database, repo_dir: str):
        self.sandbox = sandbox
        self.job_id = job_id
        self.db = db
        self.repo_dir = repo_dir
        self._cmd_str = "pnpm build"  # Default command string for Aider's string representation

    def execute(self, command: str, capture_output: bool = True) -> Tuple[int, List[str]]:
        """
        Execute a command in the sandbox and return exit code and output lines.
        
        Args:
            command: Command string to execute
            capture_output: Whether to capture and return command output
            
        Returns:
            Tuple of (exit_code, output_lines)
        """
        try:
            # Split command string into list of arguments
            if isinstance(command, str):
                command_args = command.split()
            else:
                raise ValueError(f"Command must be string, got {type(command)}")
                
            print(f"[SandboxCommandExecutor] Running command: {command}")
            process = self.sandbox.exec(
                *command_args,  # Unpack command arguments 
                workdir=self.repo_dir
            )

            output = []
            if capture_output:
                # Capture stdout
                for line in process.stdout:
                    line_str = line.strip()
                    output.append(line_str)
                    print(f"[STDOUT] {line_str}")

                # Capture stderr
                for line in process.stderr:
                    line_str = line.strip()
                    output.append(line_str)
                    print(f"[STDERR] {line_str}")

            exit_code = process.wait()
            print(f"[SandboxCommandExecutor] Command completed with exit code: {exit_code}")
            
            return exit_code, output

        except Exception as e:
            error_msg = f"Error executing command '{command}': {str(e)}"
            print(f"[SandboxCommandExecutor] {error_msg}")
            return 1

    def __call__(self, cmd: str = None) -> Optional[str]:
        """
        Makes class callable as required by Aider's test command interface.
        Returns None on success or error message on failure.
        """
        try:
            cmd_to_run = cmd or self._cmd_str
            exit_code, output = self.execute(cmd_to_run)

            # Return None for success, error message for failure (Aider requirement)
            if exit_code != 0:
                error_msg = "\n".join(output)
                return error_msg
            return None

        except Exception as e:
            error_msg = f"Error running command in sandbox: {str(e)}"
            print(f"[SandboxCommandExecutor] {error_msg}")
            return error_msg

    def __str__(self) -> str:
        """String representation for Aider's logging and display"""
        return self._cmd_str

    def __add__(self, other: str) -> str:
        """Support string concatenation for Aider's output formatting"""
        return str(self) + other

    def __radd__(self, other: str) -> str:
        """Support string concatenation from the left for Aider's output formatting"""
        return other + str(self)
