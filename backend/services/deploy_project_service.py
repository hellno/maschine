import os
import time
import requests
import json
from datetime import datetime
from backend.integrations.db import Database
from backend.services.code_service import CodeService
from backend.services.vercel_build_service import VercelBuildService
from backend.utils.farcaster import generate_domain_association
from backend.types import UserContext
from backend.services.prompts import FIX_PROBLEMS_PROMPT

DEPLOYMENT_COMPLETE_COMMIT_MESSAGE = "Deployment complete"


class DeployProjectService:
    def __init__(self, project_id: str, job_id: str, user_context: UserContext):
        self.project_id = project_id
        self.job_id = job_id
        self.user_context = user_context
        self.db = Database()
        self.project = self.db.get_project(project_id)
        self.code_service = CodeService(project_id, job_id, user_context)
        self.vercel_service = VercelBuildService(project_id)

    def run(self):
        """Execute final deployment steps"""
        try:
            self._log("Starting final deployment checks")
            self.db.update_project(self.project_id, {"status": "deploying"})
            self._update_metadata()
            self._setup_domain_association()
            self._ensure_build_success()

            self._push_commit_to_show_deployment_is_done()
            self._wait_for_vercel_build()

            self.db.update_project(
                self.project_id,
                {
                    "status": "deployed",
                },
            )
            self.db.update_job_status(self.job_id, "completed")
            self._log("Deployment completed successfully")

            # import on top of file fails even though we have farcaster-py installed
            from backend.integrations.neynar import NeynarPost
            from backend.integrations.farcaster_notifications import send_notification

            send_notification(
                fid=self.user_context["fid"],
                title=f"Your {self.project.get('name')} frame is ready!",
                body="@maschine deployed your frame 🚀",
            )
            parent_hash = self.project.get("data", {}).get("cast", {}).get("hash")
            url = self.project.get("frontend_url")
            if parent_hash and url:
                user_fid = self.project.get("fid_owner")
                NeynarPost().reply_to_cast(
                    text=f"your frame is ready! 🚀 {url}",
                    parent_hash=parent_hash,
                    parent_fid=user_fid,
                    embeds=[{"url": url}],
                )
            self.code_service.terminate_sandbox()
        except Exception as e:
            self.code_service.terminate_sandbox()
            self._log(f"Deployment failed: {str(e)}", "error")
            self.db.update_project(self.project_id, {"status": "deploy_failed"})
            raise

    def _update_metadata(self):
        """Update metadata in code to reflect project setup"""
        self._log("Updating project metadata")
        project_name = self.project.get("name")
        metadata_prompt = get_metadata_prompt(project_name)
        self._run_code_update(metadata_prompt)

    def _ensure_build_success(self):
        """Guarantee build passes with retries"""
        MAX_FIX_ATTEMPTS = 3
        for attempt in range(MAX_FIX_ATTEMPTS):
            has_errors, logs = self.code_service._run_build_in_sandbox()
            if not has_errors:
                print("deploy project service: build success in attempt", attempt)
                return
            self._run_code_update(
                f'{FIX_PROBLEMS_PROMPT}: logs:\n{logs}'
            )
        raise Exception("Failed to resolve build errors after 3 attempts")

    def _push_commit_to_show_deployment_is_done(self):
        self.code_service._create_commit(DEPLOYMENT_COMPLETE_COMMIT_MESSAGE)
        self.code_service._sync_git_changes()
        self.code_service._create_build_and_poll_status_async()

    def _wait_for_vercel_build(self):
        """Wait for Vercel build to complete using service"""
        latest_commit_sha = self.code_service._get_latest_commit_sha()
        self._log(f"Waiting for Vercel build completion for {latest_commit_sha}")

        build_status = self.vercel_service.poll_build_status(commit_hash=latest_commit_sha)

        if build_status["status"] != "success":
            error = build_status.get("error", "Unknown error")
            raise Exception(f"Vercel build failed: {error}")

    def _setup_domain_association(self):
        """setup domain association for farcaster frame v2 to reflect user connection to new vercel domain"""
        self._log("Setting up domain association")
        print("should call update_code function via modal lookup here")
        domain = self.project.get("frontend_url").replace("https://", "")
        domain_association = generate_domain_association(domain)
        update_domain_association_prompt = f"""
        Update src/app/.well-known/farcaster.json/route.ts so that the 'accountAssociation' field returns the following domain association:
        {json.dumps(domain_association, indent=2)}
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
