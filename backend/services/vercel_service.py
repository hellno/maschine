import os
import time
import requests
import git
from backend.utils.github_utils import parse_github_url
from git import Repo
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.db import Database
from backend.utils.helpers import generate_random_secret

class VercelService:
    """Handles all Vercel-related operations with retries and error handling."""

    def __init__(self, config: dict, db: Database, repo: Repo, job_id: str):
        self.config = config
        self.db = db
        self.job_id = job_id
        self.headers = {
            "Authorization": f"Bearer {config['TOKEN']}",
            "Content-Type": "application/json",
        }
        self.base_url = "https://api.vercel.com/v9"

    def create_project(self, project_name: str, repo: git.Repo) -> dict:
        """Create a Vercel project with environment setup and deployment verification."""
        try:
            # Parse GitHub URL using shared utility
            remote_url = repo.remotes.origin.url
            org_name, repo_name = parse_github_url(remote_url)
            repo_full_name = f"{org_name}/{repo_name}"

            # Check if project already exists
            existing = self._get_project(project_name)
            if existing:
                return existing

            project_data = {
                "name": project_name,
                "framework": self.config["FRAMEWORK"],
                "gitRepository": {
                    "type": "github",
                    "repo": repo_full_name,
                    "productionBranch": "main",
                },
                "installCommand": self.config["INSTALL_CMD"],
                "buildCommand": self.config["BUILD_CMD"],
                "outputDirectory": self.config["OUTPUT_DIR"],
            }

            response = requests.post(
                f"{self.base_url}/projects",
                params={"teamId": self.config["TEAM_ID"]},
                headers=self.headers,
                json=project_data,
            )

            if not response.ok:
                raise Exception(f"Failed to create project: {response.text}")

            vercel_project = response.json()
            self.db.add_log(self.job_id, "vercel", f"Created project: {repo_name}")

            # Set up environment variables
            self._setup_env_vars(repo_name)

            # Trigger initial deployment
            deployment = self._trigger_deployment(repo_name)
            if deployment:
                self._wait_for_deployment(deployment["id"])

            return vercel_project

        except Exception as e:
            self.db.add_log(self.job_id, "vercel", f"Error creating project: {str(e)}")
            raise

    def _get_project(self, name: str) -> Optional[dict]:
        """Get project details if it exists."""
        try:
            response = requests.get(
                f"{self.base_url}/projects/{name}",
                params={"teamId": self.config["TEAM_ID"]},
                headers=self.headers,
            )
            return response.json() if response.ok else None
        except Exception:
            return None

    def _setup_env_vars(self, project_name: str) -> None:
        """Set up required environment variables with retry logic."""
        env_vars = [
            {
                "key": "NEXTAUTH_SECRET",
                "value": generate_random_secret(),
                "type": "encrypted",
                "target": ["production", "preview", "development"],
            },
            {
                "key": "KV_REST_API_URL",
                "value": os.environ["KV_REST_API_URL"],
                "type": "encrypted",
                "target": ["production", "preview", "development"],
            },
            {
                "key": "KV_REST_API_TOKEN",
                "value": os.environ["KV_REST_API_TOKEN"],
                "type": "encrypted",
                "target": ["production", "preview", "development"],
            },
            {
                "key": "NEYNAR_API_KEY",
                "value": os.environ["NEYNAR_API_KEY"],
                "type": "encrypted",
                "target": ["production", "preview", "development"],
            },
        ]

        for env_var in env_vars:
            self._set_env_var(project_name, env_var)

    def _set_env_var(self, project_name: str, env_var: dict) -> None:
        """Set a single environment variable with error handling."""
        try:
            response = requests.post(
                f"{self.base_url}/projects/{project_name}/env",
                params={"teamId": self.config["TEAM_ID"]},
                headers=self.headers,
                json=env_var,
            )

            if not response.ok:
                self.db.add_log(
                    self.job_id,
                    "vercel",
                    f"Failed to set {env_var['key']}: {response.text}",
                )
            else:
                self.db.add_log(
                    self.job_id, "vercel", f"Set environment variable: {env_var['key']}"
                )
        except Exception as e:
            self.db.add_log(
                self.job_id, "vercel", f"Error setting {env_var['key']}: {str(e)}"
            )

    def _trigger_deployment(self, project_name: str) -> Optional[dict]:
        """Trigger a new deployment."""
        try:
            response = requests.post(
                f"{self.base_url}/deployments",
                params={"teamId": self.config["TEAM_ID"]},
                headers=self.headers,
                json={
                    "name": project_name,
                    "target": "production",
                    "gitSource": {"type": "github", "ref": "main"},
                },
            )

            if response.ok:
                deployment = response.json()
                self.db.add_log(
                    self.job_id, "vercel", f"Triggered deployment: {deployment['id']}"
                )
                return deployment
            return None
        except Exception as e:
            self.db.add_log(
                self.job_id, "vercel", f"Error triggering deployment: {str(e)}"
            )
            return None

    def _wait_for_deployment(self, deployment_id: str, timeout: int = 300) -> bool:
        """Wait for deployment to complete."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/deployments/{deployment_id}",
                    params={"teamId": self.config["TEAM_ID"]},
                    headers=self.headers,
                )

                if response.ok:
                    status = response.json().get("state")
                    if status == "READY":
                        self.db.add_log(
                            self.job_id, "vercel", "Deployment completed successfully"
                        )
                        return True
                    elif status in ["ERROR", "CANCELED"]:
                        self.db.add_log(
                            self.job_id,
                            "vercel",
                            f"Deployment failed with status: {status}",
                        )
                        return False

                time.sleep(10)
            except Exception as e:
                self.db.add_log(
                    self.job_id, "vercel", f"Error checking deployment status: {str(e)}"
                )

        self.db.add_log(
            self.job_id, "vercel", f"Deployment timed out after {timeout} seconds"
        )
        return False
