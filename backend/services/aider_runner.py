"""
Aider code generation service with enhanced error handling and context management
"""
import os
import time
from typing import Optional, Dict
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from backend import config
from backend.exceptions import (
    AiderError, AiderTimeoutError, AiderExecutionError, CodeServiceError
)
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
    "spec.md",
]

class AiderRunner:
    """Orchestrates Aider code generation with enhanced error handling"""

    def __init__(
        self,
        job_id: str,
        project_id: str,
        user_context: Optional[Dict] = None
    ):
        self.job_id = job_id
        self.project_id = project_id
        self.user_context = user_context
        self.context_enhancer = CodeContextEnhancer()

    def create_aider_coder(self, repo_dir: str) -> Coder:
        """Configure and initialize Aider coder instance"""
        try:
            fnames = [os.path.join(repo_dir, f) for f in DEFAULT_PROJECT_FILES]
            read_only_fnames = READONLY_FILES

            io = InputOutput(yes=True, root=repo_dir)
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
            raise AiderError(error_msg, self.job_id, self.project_id, e)

    def run_aider(self, coder: Coder, prompt: str, timeout: int = 120) -> str:
        """
        Execute Aider with proper timeout and retry handling

        Args:
            coder: Configured Aider instance
            prompt: Code generation prompt
            timeout: Seconds before timing out

        Returns:
            Aider result string

        Raises:
            AiderTimeoutError: If process exceeds timeout
            AiderExecutionError: For execution failures
        """
        try:
            return self._run_with_retries(
                coder.run,
                args=(prompt,),
                max_retries=3,
                retry_delay=15,
                timeout=timeout
            )
        except AiderTimeoutError as e:
            raise
        except Exception as e:
            raise AiderExecutionError(self.job_id, self.project_id, e)

    def enhance_prompt_with_context(self, prompt: str) -> str:
        """Enhance user prompt with relevant code context"""
        try:
            context = self.context_enhancer.get_relevant_context(prompt)
            if context:
                return f"Context:\n{context}\n\nPrompt: {prompt}"
            return prompt
        except Exception as e:
            print(f"Context enhancement failed: {str(e)}")
            return prompt

    def generate_fix_for_errors(self, error_logs: str) -> str:
        """Generate LLM prompt to fix build errors"""
        truncated_logs = error_logs[:2000]  # Stay under token limits
        return (
            f"The build failed with these errors:\n{truncated_logs}\n\n"
            "Please analyze these errors and suggest specific code changes to fix them. "
            "Focus on these areas:\n"
            "1. Missing dependencies\n"
            "2. Syntax errors\n"
            "3. Configuration issues\n"
            "Provide complete code solutions with minimal changes."
        )

    def _run_with_retries(
        self,
        target,
        args=(),
        max_retries: int = 3,
        retry_delay: int = 15,
        timeout: int = 240
    ) -> str:
        """Internal retry handler with process management"""
        import multiprocessing
        from queue import Empty

        def target_wrapper(queue, *args):
            try:
                result = target(*args)
                queue.put(('success', result))
            except Exception as e:
                queue.put(('error', e))

        for attempt in range(max_retries):
            queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=target_wrapper,
                args=(queue,) + args,
                daemon=True
            )
            process.start()

            try:
                process.join(timeout=timeout)

                if process.is_alive():
                    process.terminate()
                    time.sleep(1)
                    if process.is_alive():
                        process.kill()
                    raise AiderTimeoutError(self.job_id, self.project_id, timeout)

                result_type, result_data = queue.get_nowait()
                if result_type == 'success':
                    return result_data
                raise result_data

            except AiderTimeoutError:
                print(f'aider timed out on job {self.job_id} in project {self.project_id}: attempt {attempt}')
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
            except Empty:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise AiderExecutionError(
                    self.job_id, self.project_id,
                    RuntimeError("Process returned no result")
                )
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise AiderExecutionError(self.job_id, self.project_id, e)

        raise AiderError(
            f"Failed after {max_retries} attempts",
            self.job_id,
            self.project_id
        )
