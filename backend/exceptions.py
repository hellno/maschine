"""
Custom exceptions for the code service with rich context tracking
"""
from typing import Optional

class CodeServiceError(Exception):
    """Base exception for all code service related errors"""
    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        project_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        self.job_id = job_id
        self.project_id = project_id
        self.original_exception = original_exception
        self.message = message
        super().__init__(message)

    def __str__(self):
        return (
            f"{self.message}\n"
            f"Context: job={self.job_id}, project={self.project_id}\n"
            f"Original exception: {type(self.original_exception).__name__}: {str(self.original_exception)}"
        )

class SandboxError(CodeServiceError):
    """Base exception for sandbox-related errors"""
    pass

class SandboxCreationError(SandboxError):
    """Failed to create sandbox environment"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to create sandbox environment",
            job_id,
            project_id,
            original_exception
        )

class SandboxTerminationError(SandboxError):
    """Failed to terminate sandbox environment"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to terminate sandbox environment",
            job_id,
            project_id,
            original_exception
        )

class GitError(CodeServiceError):
    """Base exception for Git-related errors"""
    pass

class GitCloneError(GitError):
    """Failed to clone repository"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to clone Git repository",
            job_id,
            project_id,
            original_exception
        )

class GitPushError(GitError):
    """Failed to push changes to remote repository"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to push Git changes",
            job_id,
            project_id,
            original_exception
        )

class BuildError(CodeServiceError):
    """Base exception for build process errors"""
    pass

class InstallError(BuildError):
    """Failed to install dependencies"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to install project dependencies",
            job_id,
            project_id,
            original_exception
        )

class CompileError(BuildError):
    """Failed to compile/build project"""
    def __init__(self, job_id: str, project_id: str, logs: str):
        super().__init__(
            f"Build failed with errors: {logs}",
            job_id,
            project_id
        )
        self.logs = logs

class AiderError(CodeServiceError):
    """Base exception for Aider-related errors"""
    pass

class AiderTimeoutError(AiderError):
    """Aider process timed out"""
    def __init__(self, job_id: str, project_id: str, timeout: int):
        super().__init__(
            f"Aider process timed out after {timeout} seconds",
            job_id,
            project_id
        )
        self.timeout = timeout

class AiderExecutionError(AiderError):
    """Error during Aider execution"""
    def __init__(self, job_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            "Error during Aider code generation",
            job_id,
            project_id,
            original_exception
        )

class VercelBuildError(CodeServiceError):
    """Base exception for Vercel build-related errors"""
    pass

class VercelAPIError(VercelBuildError):
    """Error communicating with Vercel API"""
    def __init__(self, job_id: Optional[str], project_id: str, original_exception: Exception):
        super().__init__(
            "Failed to communicate with Vercel API",
            job_id,
            project_id,
            original_exception
        )

class VercelBuildPollingError(VercelBuildError):
    """Error during build status polling"""
    def __init__(self, build_id: str, project_id: str, original_exception: Exception):
        super().__init__(
            f"Build status polling failed for build {build_id}",
            None,  # job_id not applicable
            project_id,
            original_exception
        )
        self.build_id = build_id
