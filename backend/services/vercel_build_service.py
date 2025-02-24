import os
import requests
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from backend.integrations.db import Database


class VercelBuildService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.db = Database()
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID")

    def _get_vercel_project_id(self) -> Optional[str]:
        """Get Vercel project ID from database"""
        project = self.db.get_project(self.project_id)
        return project.get("vercel_project_id")

    def get_vercel_build_status(self, commit_hash: str) -> Dict:
        """
        Fetch Vercel build status for a specific commit
        Returns: {
            "status": "queued|building|ready|error",
            "url": str,
            "logs": list,
            "created_at": datetime
        }
        """
        vercel_project_id = self._get_vercel_project_id()
        if not vercel_project_id:
            return {"error": "Project not configured with Vercel"}

        headers = {"Authorization": f"Bearer {self.vercel_token}"}
        params = {
            "projectId": vercel_project_id,
            "teamId": self.team_id,
            "target": "production",
            "metaGithubCommitSha": commit_hash,
        }

        try:
            response = requests.get(
                "https://api.vercel.com/v6/deployments", headers=headers, params=params
            )
            response.raise_for_status()

            deployments = response.json().get("deployments", [])
            if not deployments:
                return {"status": "queued", "message": "Build not yet started"}

            deployment = deployments[0]
            return self._parse_deployment(deployment)

        except requests.exceptions.RequestException as e:
            print(f"Vercel API error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _parse_deployment(self, deployment: Dict) -> Dict:
        """Map Vercel deployment to our status format"""
        print(f"parsing vercel deployment: {deployment}")
        status_map = {
            "BUILDING": "building",
            "INITIALIZING": "building",
            "QUEUED": "queued",
            "READY": "success",
            "ERROR": "error",
        }

        return {
            "status": status_map.get(deployment.get("state", "").upper(), "unknown"),
            "url": deployment.get("url"),
            "created_at": deployment.get("createdAt"),
            "logs_url": f"https://api.vercel.com/v2/deployments/{deployment['uid']}/events",
            "deployment_id": deployment.get("uid")
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def get_deployment_by_id(self, deployment_id: str) -> Dict:
        """Get deployment details directly by Vercel ID with retries"""
        headers = {"Authorization": f"Bearer {self.vercel_token}"}
        params = {"teamId": self.team_id}
        
        try:
            response = requests.get(
                f"https://api.vercel.com/v13/deployments/{deployment_id}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": "Deployment not found"}
            raise
