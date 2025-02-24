import os
import requests
from typing import Optional, Dict
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
        }
