import os
import requests
from typing import Dict
from backend.db import Database
from backend.utils.helpers import generate_random_secret


class VercelService:
    """Handles all Vercel-related operations."""

    def __init__(self, config: dict, db: Database, job_id: str):
        self.config = config
        self.db = db
        self.job_id = job_id
        self.headers = {
            "Authorization": f"Bearer {config['TOKEN']}",
            "Content-Type": "application/json",
        }

    def create_project(self, repo_name: str, repo: object) -> dict:
        """Create a Vercel project with environment setup."""
        project_data = {
            "name": repo_name,
            "framework": self.config["FRAMEWORK"],
            "gitRepository": {
                "type": "github",
                "repo": repo.full_name,
            },
            "installCommand": self.config["INSTALL_CMD"],
            "buildCommand": self.config["BUILD_CMD"],
            "outputDirectory": self.config["OUTPUT_DIR"],
        }

        vercel_project = requests.post(
            f"https://api.vercel.com/v9/projects?teamId={
                self.config['TEAM_ID']}",
            headers=self.headers,
            json=project_data,
        ).json()

        if "error" in vercel_project:
            raise Exception(f"Failed to create Vercel project: {
                            vercel_project['error']}")

        self.db.add_log(self.job_id, "vercel", "Created Vercel project")
        self.setup_env_vars(repo_name)

        return vercel_project

    def setup_env_vars(self, repo_name: str) -> None:
        """Set up required environment variables."""
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
            self._set_env_var(repo_name, env_var)

    def _set_env_var(self, repo_name: str, env_var: dict) -> None:
        """Set a single environment variable."""
        response = requests.post(
            f"https://api.vercel.com/v9/projects/{
                repo_name}/env?teamId={self.config['TEAM_ID']}",
            headers=self.headers,
            json=env_var,
        ).json()

        if "error" in response:
            self.db.add_log(
                self.job_id,
                "vercel",
                f"Warning: Failed to set env var {
                    env_var['key']}: {response['error']}"
            )
