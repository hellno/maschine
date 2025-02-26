import os
import time
import requests
from typing import Optional, Dict, Literal
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from backend.integrations.db import Database

status_map = {
    "BUILDING": "building",
    "INITIALIZING": "building",
    "QUEUED": "queued",
    "READY": "success",
    "ERROR": "error"
}

BuildStatus = Literal['building', 'queued', 'success', 'error']

class VercelBuildService:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.db = Database()
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID")

        # Configure polling parameters
        self.max_polling_attempts = 30  # 5 minutes with 10s interval
        self.poll_interval = 10  # seconds

    def _get_vercel_project_id(self) -> Optional[str]:
        """Get Vercel project ID from database"""
        if not hasattr(self, "_project"):
            self._project = self.db.get_project(self.project_id)

        return self._project.get("vercel_project_id")

    def get_vercel_build_by_commit_hash(self, commit_hash: str) -> Dict:
        """
        Fetch Vercel build status for a specific commit
        Returns: {
            "id": str,
            "status": BuildStatus,
            "url": str,
            "created_at": str
            "finished_at": str,
            "data": dict
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
                "https://api.vercel.com/v6/deployments", headers=headers, params=params # this works with metaGithubCommitSha
            )
            response.raise_for_status()

            deployments = response.json().get("deployments", [])
            print(f'got vercel deployments with metaGithubCommitSha {commit_hash}: {len(deployments)}')
            if not deployments:
                return {"status": "queued", "message": "Build not yet started"}

            deployments_with_commit_hash = [d for d in deployments if d['meta']['githubCommitSha'] == commit_hash]
            if not deployments_with_commit_hash:
                print(f'No deployment found for commit hash {commit_hash}, but has {len(deployments)} deployments')
                return {"status": "queued", "message": "Build not yet started"}

            deployment = deployments_with_commit_hash[0]
            return self._parse_deployment(deployment)

        except requests.exceptions.RequestException as e:
            print(f"Vercel API error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _parse_deployment(self, deployment: Dict) -> Dict:
        # ai!
        # getting this error when trying to write the parsed values to DB:
        # Error polling build status: {'code': '22008', 'details': None, 'hint': 'Perhaps you need a different "datestyle" setting.', 'message': 'date/time field value out of range: "1740567255067"'}
        if "readyState" in deployment:
            return {
                "status": status_map.get(deployment.get("readyState", "").upper(), "unknown"),
                "vercel_build_id": deployment.get("uid"),
                "finished_at": deployment.get("ready"),
                "data": deployment
            }

        # Handle v6 deployment format
        print(f'parsing v6 deployment data: {deployment}')
        return {
            "status": status_map.get(deployment.get("state", "").upper(), "unknown"),
            "vercel_build_id": deployment.get("uid"),
            "finished_at": deployment.get("ready"),
            "data": deployment
        }

    def get_vercel_build_by_vercel_build_id(self, vercel_build_id: str) -> Dict:
        """Get deployment details directly by Vercel ID with retries
        Uses vercel deployment id, not the DB 'builds' table id
        """

        vercel_project_id = self._get_vercel_project_id()
        headers = {"Authorization": f"Bearer {self.vercel_token}"}
        params = {
            "projectId": vercel_project_id,
            "teamId": self.team_id,
            "target": "production",
        }

        try:
            print(f'get vercel deployment with id {vercel_build_id}')
            response = requests.get(
                f"https://api.vercel.com/v13/deployments/{vercel_build_id}",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            deployments = response.json().get("deployments", [])
            print(f'got vercel deployments with id {vercel_build_id}: {len(deployments)}')
            deployments_with_build_id = [d for d in deployments if d['uid'] == vercel_build_id]
            if not deployments_with_build_id:
                print(f'No deployment found for id {vercel_build_id}')
                return {"status": "queued", "message": "Build not yet started"}

            deployment = deployments_with_build_id[0]
            return self._parse_deployment(deployment)

            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": "Deployment not found"}
            raise

    def poll_build_status(self, build_id: Optional[str] = None, commit_hash: Optional[str] = None) -> Dict:
        """
        Poll for build status updates and update the database

        Args:
            build_id: ID of the build in our database
            commit_hash: Optional commit hash. If not provided, will be fetched from build record

        Returns:
            Final build status or error
        """
        if not build_id and not commit_hash:
            raise ValueError("Either build_id or commit_hash must be provided")

        print(f'[vercel_build_service] Starting build polling for build id {build_id} and commit hash {commit_hash}')

        attempts = 0
        build_db = None
        initial_build = None

        if not commit_hash:
            build_db = self.db.get_build_by_id(str(build_id))
            if not build_db:
                return {"error": "Build not found"}

            deployment_id = build_db.get('vercel_build_id')
            commit_hash = build_db.get('commit_hash')
            if deployment_id:
                initial_build = self.get_vercel_build_by_vercel_build_id(str(deployment_id))
            elif commit_hash:
                initial_build = self.get_vercel_build_by_commit_hash(str(commit_hash))

        if not build_id:
            build_db = self.db.get_build_by_commit(self.project_id, str(commit_hash))
            if not build_db:
                raise ValueError("Build not found")

            build_id = build_db.get("id")
            initial_build = self.get_vercel_build_by_commit_hash(str(commit_hash))


        if not initial_build:
            raise ValueError(f"failed to get initial build state for build id {build_id} and commit hash {commit_hash}")

        print('build_db:', build_db)
        print('initial_build:', initial_build)

        initial_status = initial_build.get("status")
        if initial_status in ['success', 'error']:
            if build_db.get('status') != initial_status:
                print(f'Build status changed from {build_db.get("status")} to {initial_status} - saving changes to db')
                self.db.update_build(build_id, initial_build)
            print(f'build {build_id} has status {initial_status} - no need to keep polling')
            return initial_build

        while attempts < self.max_polling_attempts:
            try:
                print(f'[vercel_build_service] {build_id} Polling attempt {attempts+1}')

                if build_id:
                    print(f'[vercel_build_service] {build_id} Using build id: {build_id}')
                    build = self.get_vercel_build_by_vercel_build_id(build_id)
                else:
                    build = self.get_vercel_build_by_commit_hash(str(commit_hash))
                    if 'build_id' in build:
                        build_id = build.get("build_id")

                status = build.get("status")
                if status in ['success', 'error']:
                    print(f'build {build_id} has status {status} - initial state before polling: {initial_status}')
                    self.db.update_build(str(build_id), build)
                    print(f'build {build_id} has status {initial_status} - no need to keep polling')
                    return initial_build

            except Exception as e:
                error_msg = f"Polling error: {str(e)}"
                print(f"[vercel_build_service] {build_id} {error_msg}")
                self.db.add_build_log(str(build_id), "vercel", error_msg)

            attempts += 1
            time.sleep(self.poll_interval)

        # If we reach here, polling timed out
        timeout_msg = "Build status polling timed out"
        # self.db.update_build_status(build_id, "failed", timeout_msg)
        # self.db.add_build_log(build_id, "vercel", timeout_msg)
        return {"status": "failed", "error": timeout_msg}

    def _parse_status_from_deployment(self, deployment: Dict) -> Dict:
        """Convert Vercel deployment status to our format with error handling"""
        state = deployment.get("readyState", "").upper() or deployment.get("state", "").upper()

        if state == "READY":
            return {"status": "success"}
        elif state == "ERROR":
            error_msg = deployment.get("errorMessage") or "Unknown error"
            return {"status": "failed", "error": error_msg}
        elif state in ["BUILDING", "INITIALIZING"]:
            return {"status": "building"}
        elif state == "QUEUED":
            return {"status": "queued"}
        else:
            return {"status": "unknown"}
