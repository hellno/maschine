import base64
import os
import requests
from backend.integrations.db import Database
from typing import Optional

VERCEL_CONFIG = {
    "FRAMEWORK": "nextjs",
    "INSTALL_CMD": "pnpm install",
    "BUILD_CMD": "pnpm build",
    "OUTPUT_DIR": ".next",
}


class VercelApi:
    """Handles all Vercel-related operations with retries and error handling."""

    def __init__(self, project_id: str, job_id: Optional[str] = None):
        self.project_id = project_id
        self.job_id = job_id
        self.vercel_team_id = os.environ["VERCEL_TEAM_ID"]
        self.vercel_token = os.environ["VERCEL_TOKEN"]
        self.headers = {
            "Authorization": f"Bearer {self.vercel_token}",
            "Content-Type": "application/json",
        }

        self.db = Database()

    def create_project(self, project_name: str, repo_full_name: str):
        vercel_project = self._create_vercel_project(
            project_name, repo_full_name=repo_full_name
        )

        github_repo_id = vercel_project["link"]["repoId"]
        vercel_project_id = vercel_project["id"]
        update_project_data = dict(
            github_repo_id=github_repo_id, vercel_project_id=vercel_project_id
        )
        self.db.update_project(self.project_id, update_project_data)

        self._deploy_vercel_project(project_name, github_repo_id)
        self._store_frontend_url(project_name)

    def _create_vercel_project(self, project_name: str, repo_full_name: str) -> dict:
        """Create a Vercel project with environment setup and deployment verification.
        @param project_name: Name of the project
        @param repo_full_name: Full name of the GitHub repository = org/repo_name
        """

        try:
            existing = self._get_project(project_name)
            if existing:
                print(f"project {project_name} already exists", existing)
                return existing

            project_data = {
                "name": project_name,
                "framework": VERCEL_CONFIG["FRAMEWORK"],
                "gitRepository": {
                    "type": "github",
                    "repo": repo_full_name,
                    "productionBranch": "main",
                },
                "installCommand": VERCEL_CONFIG["INSTALL_CMD"],
                "buildCommand": VERCEL_CONFIG["BUILD_CMD"],
                "outputDirectory": VERCEL_CONFIG["OUTPUT_DIR"],
                "environmentVariables": [
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
                    {
                        "key": "DUNE_API_KEY",
                        "value": os.environ["DUNE_API_KEY"],
                        "type": "encrypted",
                        "target": ["production", "preview", "development"],
                    },
                    {
                        "key": "NEXT_PUBLIC_POSTHOG_KEY",
                        "value": os.environ["NEXT_PUBLIC_POSTHOG_KEY"],
                        "type": "encrypted",
                        "target": ["production"],
                    },
                    {
                        "key": "NEXT_PUBLIC_POSTHOG_HOST",
                        "value": os.environ["NEXT_PUBLIC_POSTHOG_HOST"],
                        "type": "encrypted",
                        "target": ["production"],
                    },
                ],
            }
            print(f'creating vercel project with project data {project_data}')
            response = requests.post(
                "https://api.vercel.com/v11/projects",
                params={"teamId": self.vercel_team_id},
                headers=self.headers,
                json=project_data,
            )

            if not response.ok:
                print(f"Failed to create project: {response.text}")
                raise Exception(f"Failed to create project: {response.text}")

            vercel_project = response.json()
            print("create vercel project response", vercel_project)
            if self.job_id:
                self.db.add_log(self.job_id, "vercel", f"created project {repo_full_name}")
            return vercel_project
        except Exception as e:
            print(f'Error creating project: {str(e)}')
            if self.job_id:
                self.db.add_log(self.job_id, "vercel", f"Error creating project: {str(e)}")
            raise

    def _deploy_vercel_project(self, project_name: str, github_repo_id: str):
        try:
            self._trigger_deployment(project_name, github_repo_id)
        except Exception as e:
            print(f'Error deploying project: {str(e)}')
            if self.job_id:
                self.db.add_log(self.job_id, "vercel", f"Error deploying project: {str(e)}")
            raise

    def _get_project(self, name: str) -> Optional[dict]:
        """Get project details if it exists."""
        try:
            response = requests.get(
                f"https://api.vercel.com/v9/projects/{name}",
                params={"teamId": self.vercel_team_id},
                headers=self.headers,
            )
            return response.json() if response.ok else None
        except Exception as e:
            print(f"Error fetching project: {str(e)}")
            return None

    def _store_frontend_url(self, vercel_project_id: str):
        try:
            response = requests.get(
                f"https://api.vercel.com/v9/projects/{vercel_project_id}/domains",
                params={"teamId": self.vercel_team_id},
                headers=self.headers,
            )

            if not response.ok:
                raise Exception(f"Failed to fetch domains: {response.text}")

            domains = response.json().get("domains", [])
            if not domains:
                raise Exception("No domains found for project")
            print("domains", domains)
            # Get the shortest domain name from the list
            custom_domain = min((domain["name"] for domain in domains), key=len)

            domain_env_var = {
                "key": "NEXT_PUBLIC_URL",
                "value": f"https://{custom_domain}",
                "type": "plain",
                "target": [
                    "production",
                ],
            }
            self._set_env_var(vercel_project_id, domain_env_var)
            if self.job_id:
                self.db.add_log(
                self.job_id, "vercel", f"Set custom domain: {custom_domain}"
            )
            self.db.update_project(
                self.project_id, {"frontend_url": f"https://{custom_domain}"}
            )
        except Exception as e:
            print(f'Error setting custom domain: {str(e)}')
            if self.job_id:
                self.db.add_log(
                self.job_id, "vercel", f"Error setting frontend URL: {str(e)}"
            )
            raise

    def _set_env_var(self, project_name: str, env_var: dict) -> None:
        """Set a single environment variable with error handling."""
        try:
            response = requests.post(
                f"https://api.vercel.com/v9/projects/{project_name}/env",
                params={"teamId": self.vercel_team_id},
                headers=self.headers,
                json=env_var,
            )

            if not response.ok:
                print(
                    f"Failed to set {env_var['key']}: {response.text}",
                )
            else:
                print(f"Set environment variable: {env_var['key']}")
        except Exception as e:
            print(f'Error setting environment variable: {env_var["key"]}: {str(e)}')
            if self.job_id:
                self.db.add_log(
                    self.job_id, "vercel", f"Error setting {env_var['key']}: {str(e)}"
                )

    def _trigger_deployment(
        self, project_name: str, github_repo_id: str
    ) -> Optional[dict]:
        try:
            payload = {
                "name": "test",
                "target": "production",
                "gitSource": {
                    "type": "github",
                    "ref": "main",
                    "repoId": github_repo_id,
                },
            }
            print(f'triggering a vercel deployment with payload: {payload}')
            response = requests.post(
                "https://api.vercel.com/v13/deployments",
                params={"teamId": self.vercel_team_id},
                headers=self.headers,
                json=payload,
            )

            if response.ok:
                deployment = response.json()
                print(f"triggering a deployment worked: {deployment}")
                if self.job_id:
                    self.db.add_log(
                        self.job_id, "vercel", f"Triggered deployment: {deployment['id']}"
                    )
                return deployment
            else:
                print(f"trigger deployment failed: {response.text}")
                raise Exception(f"Failed to trigger deployment: {response.text}")
        except Exception as e:
            print(f'Error triggering deployment: {str(e)}')
            if self.job_id:
                self.db.add_log(
                    self.job_id, "vercel", f"Error triggering deployment: {str(e)}"
                )
            return None


def generate_random_secret() -> str:
    """Generate a cryptographically secure random secret"""
    return base64.b64encode(os.urandom(32)).decode("utf-8")
