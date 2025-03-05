import os
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Literal
from backend.integrations.db import Database
from backend.config import SETUP_COMPLETE_COMMIT_MESSAGE
from backend.integrations.farcaster_notifications import send_notification

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
        self.max_polling_attempts = 60  # 5 minutes with 10s interval
        self.poll_interval = 15  # seconds

    def _get_project(self):
        if not hasattr(self, "_project"):
            self._project = self.db.get_project(self.project_id)

        return self._project


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
        print(f'get_vercel_build_by_commit_hash: {commit_hash}')
        vercel_project_id = self._get_project().get("vercel_project_id")
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
            data = response.json()
            print('data', data)
            deployments = data.get("deployments", [])
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
        """Parse Vercel deployment data into our format, converting timestamps to ISO format"""
        del deployment['creator'] # has personal data we don't need
        result = {
            "vercel_build_id": deployment.get("uid"),
            "data": deployment
        }

        # Handle readyState format (v13 API)
        if "readyState" in deployment:
            result["status"] = status_map.get(deployment.get("readyState", "").upper(), "unknown")
        # Handle state format (v6 API)
        else:
            print(f'parsing v6 deployment data: {deployment}')
            result["status"] = status_map.get(deployment.get("state", "").upper(), "unknown")

        ready_timestamp = deployment.get("ready")
        if ready_timestamp:
            try:
                timestamp_seconds = int(float(ready_timestamp)) / 1000.0
                # Convert to ISO format
                iso_date = datetime.fromtimestamp(timestamp_seconds).isoformat()
                result["finished_at"] = iso_date
            except Exception as e:
                # Don't include the timestamp if we can't convert it
                print(f"Error converting timestamp {ready_timestamp}: {e}")

        print(f'parsed result:', result)
        return result

    def get_vercel_build_by_vercel_build_id(self, vercel_build_id: str) -> Optional[Dict]:
        """Get deployment details directly by Vercel ID with retries
        Uses vercel deployment id, not the DB 'builds' table id
        """
        print(f'get_vercel_build_by_vercel_build_id: {vercel_build_id}')
        vercel_project_id = self._get_project().get("vercel_project_id")
        headers = {"Authorization": f"Bearer {self.vercel_token}"}
        params = {
            "projectId": vercel_project_id,
            "teamId": self.team_id,
            "target": "production",
        }

        try:
            response = requests.get(
                f"https://api.vercel.com/v13/deployments/{vercel_build_id}",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            print('data', data)
            deployments = data.get("deployments", [])
            print(f'got vercel deployments with id {vercel_build_id}: {len(deployments)}')
            deployments_with_build_id = [d for d in deployments if d['uid'] == vercel_build_id]
            if not deployments_with_build_id:
                print(f'No deployment found for id {vercel_build_id}')
                return None

            deployment = deployments_with_build_id[0]
            return self._parse_deployment(deployment)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
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
        initial_status = 'unknown'

        if not commit_hash:
            build_db = self.db.get_build_by_id(str(build_id))
            if not build_db:
                return {"error": "Build not found"}

            deployment_id = build_db.get('vercel_build_id')
            commit_hash = build_db.get('commit_hash')
            print(f'has no commit hash, got db entry with vercel_build_id {deployment_id} and commit_hash {commit_hash}')
            if deployment_id:
                initial_build = self.get_vercel_build_by_vercel_build_id(str(deployment_id))
            elif commit_hash:
                initial_build = self.get_vercel_build_by_commit_hash(str(commit_hash))

        if not build_id:
            build_db = self.db.get_build_by_commit(self.project_id, str(commit_hash))
            if not build_db:
                raise ValueError("Build not found")

            build_id = build_db.get("id")
            print(f'has no build id, got db entry and now know build_id {build_id}')
            initial_build = self.get_vercel_build_by_commit_hash(str(commit_hash))


        print('initial_build:', initial_build)
        print('build_db:', build_db)
        if initial_build:
            initial_status = initial_build.get("status")
            if initial_status in ['success', 'error']:
                if build_db.get('status') != initial_status:
                    print(f'Build status changed from {build_db.get("status")} to {initial_status} - saving changes to db')
                    self.db.update_build(build_id, initial_build)
                print(f'build {build_id} has status {initial_status} - no need to start polling')
                return initial_build

        while attempts < self.max_polling_attempts:
            try:
                print(f'[vercel_build_service] db build id {build_id} polling attempt {attempts+1}')
                build = self.get_vercel_build_by_commit_hash(str(commit_hash))
                if not build:
                    print(f'build based on commit hash {commit_hash} not found via vercel api')
                    time.sleep(self.poll_interval)
                    continue

                status = build.get("status")
                print('build', build)
                if status in ['success', 'error']:
                    print(f'======================================================\nbuild {build_id} changed to status {status} - no need to keep polling')
                    self.db.update_build(str(build_id), build)
                    data = build.get('data', {})
                    commit_message = data.get('meta', {}).get('githubCommitMessage', '')
                    if commit_message is SETUP_COMPLETE_COMMIT_MESSAGE:
                        project = self._get_project()
                        send_notification(
                            fid=project.get('fid_owner'),
                            title=f"@maschine created your frame {project.get('name', '')}",
                            body='your frame is ready'
                        )
                    return build

            except Exception as e:
                error_msg = f"Polling error: {str(e)}"
                print(f"[vercel_build_service] {build_id} {error_msg}")

            attempts += 1
            time.sleep(self.poll_interval)

        # If we reach here, polling timed out
        timeout_msg = "Build status polling timed out"
        # self.db.update_build_status(build_id, "failed", timeout_msg)
        # self.db.add_build_log(build_id, "vercel", timeout_msg)
        return {"status": "failed", "error": timeout_msg}
