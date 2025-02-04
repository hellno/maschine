from backend.integrations.db import Database
from backend.services.code_service import CodeService
from backend.integrations.vercel_api import VercelApi
from backend.utils.farcaster import generate_domain_association
from backend.types import UserContext
import json


class DeployProjectService:
    def __init__(self, project_id: str, job_id: str, user_context: UserContext):
        self.project_id = project_id
        self.job_id = job_id
        self.user_context = user_context
        self.db = Database()
        self.project = self.db.get_project(project_id)
        self.code_service = CodeService(project_id, job_id, user_context)

    def run(self):
        """Execute final deployment steps"""
        try:
            self._log("Starting final deployment checks")
            self.db.update_project(self.project_id, {"status": "deploying"})
            self._update_metadata()
            self._setup_domain_association()
            self._ensure_build_success()
            self.db.update_project(
                self.project_id,
                {
                    "status": "deployed",
                },
            )
            self.db.update_job_status(self.job_id, "completed")
            self._log("Deployment completed successfully")
        except Exception as e:
            self._log(f"Deployment failed: {str(e)}", "error")
            self.db.update_project(self.project_id, {"status": "failed"})
            raise

    def _update_metadata(self):
        """Update metadata in code to reflect project setup"""
        self._log("Updating project metadata")
        metadata_prompt = get_metadata_prompt(self.project_name)
        self._run_code_update(metadata_prompt)

    def _ensure_build_success(self):
        """Guarantee build passes with retries"""
        for attempt in range(3):
            has_errors, logs = self.code_service._run_build_in_sandbox(
                terminate_after_build=True
            )
            if not has_errors:
                return
            self._run_code_update(f"Fix build errors (attempt {attempt + 1}):\n{logs}")
        raise Exception("Failed to resolve build errors after 3 attempts")

    def _setup_domain_association(self):
        """setup domain association for farcaster frame v2 to reflect user connection to new vercel domain"""
        self._log("Setting up domain association")
        print("should call update_code function via modal lookup here")
        domain = self.project.get("frontend_url").replace("https://", "")
        domain_association = generate_domain_association(domain)
        update_domain_association_prompt = f"""
        Update src/app/.well-known/farcaster.json/route.ts so that the 'accountAssociation' field returns the following domain association:
        {json.dumps(domain_association["json"], indent=2)}
        Only update the accountAssociation field.
        """
        self._run_code_update(update_domain_association_prompt)

    def _run_code_update(self, prompt: str):
        """Helper to run code updates with error handling"""
        try:
            result = self.code_service.run(prompt)
            if result.get("status") != "success":
                raise Exception("Code update failed")
        except Exception as e:
            self._log(f"Deployment error: {str(e)}", "error")
            self.db.update_job_status(self.job_id, "failed", str(e))
            raise

    def _log(self, message: str, level: str = "info"):
        print(f"[{level.upper()}] DeployService {message}")
        self.db.add_log(self.job_id, "deploy", message)


def get_metadata_prompt(project_name: str) -> str:
    """Generate metadata update prompt."""
    return f"""
Update the following files to customize the project metadata:
1. In src/lib/constants.ts:
   set PROJECT_ID to "{project_name}"
   set PROJECT_TITLE to "{project_name}"
   set PROJECT_DESCRIPTION to a brief description of the project
2. In src/app/opengraph-image.tsx:
   - Reflect the project name "{project_name}"
   - Include a matching color or layout
   - Keep a simple one-page brand layout
"""
