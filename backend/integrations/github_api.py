import os
from typing import Optional
from github import Github
import tempfile
import git
import shutil

from backend.config import GITHUB
from backend.integrations.db import Database
from backend.utils.strings import sanitize_project_name


def get_github_instance():
    if not os.environ.get("GITHUB_TOKEN"):
        raise Exception("Missing GITHUB_TOKEN environment variable")
    return Github(os.environ["GITHUB_TOKEN"])


def clone_repo_url_to_dir(repo_url: str, dir_path: str):
    """Clone a GitHub repository to a directory"""
    # Ensure URL starts with https://github.com/
    if not repo_url.startswith('https://github.com/'):
        repo_url = f"https://github.com/{repo_url}"
    
    # Insert GitHub token for authentication
    auth_url = repo_url.replace(
        'https://github.com/',
        f'https://{os.environ["GITHUB_TOKEN"]}@github.com/'
    )
    
    # Ensure .git extension
    if not auth_url.endswith('.git'):
        auth_url += '.git'
        
    return git.Repo.clone_from(auth_url, dir_path)


def configure_git_user_for_repo(repo: git.Repo):
    """Configure git user for a repository"""

    repo.config_writer().set_value("user", "name", GITHUB["COMMIT_NAME"]).release()
    repo.config_writer().set_value("user", "email", GITHUB["COMMIT_EMAIL"]).release()


class GithubApi:
    def __init__(
        self, job_id: str, project_name: str, username: str, description: str = None
    ):
        self.job_id = job_id
        self.project_name = project_name
        self.username = username
        self.description = description or GITHUB["DEFAULT_DESCRIPTION"]
        self.repo = None

        self.db = Database()

    def create_repo(self) -> str:
        """Create GitHub repository"""

        gh = get_github_instance()

        try:
            sanitized_username = sanitize_project_name(self.username)
            repo_name = f"{sanitized_username}-{self.project_name}"

            print(f"Generated github repo name: {repo_name}")

            org = gh.get_organization(GITHUB["ORG_NAME"])
            self.repo = org.create_repo(
                name=repo_name,
                description=self.description,
                private=False,
            )

            if not self.repo:
                raise Exception("Failed to create GitHub repository")

            self.db.add_log(
                self.job_id,
                "github",
                f"Created repo: {self.repo.full_name}",
            )
            print("repooo.full_name", self.repo.full_name)
            return self.repo.full_name

        except Exception as e:
            self.db.add_log(
                self.job_id, "github", f"Fatal error creating repo: {str(e)}"
            )
            if self.repo:
                self.repo.delete()
                self.db.add_log(self.job_id, "github", "Cleaned up failed repo")
            raise

    def copy_template_to_repo(
        self, template_git_url: Optional[str] = None, repo: git.Repo = None
    ) -> None:
        """Copy template files to repository"""
        template_git_url = template_git_url or GITHUB["TEMPLATE_REPO"]

        if repo:
            self.repo = repo

        if not self.repo:
            raise Exception("Failed to copy template -> no repository to copy to")

        try:
            print("entering temp dir to copy template files")
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone template repo
                template_path = os.path.join(temp_dir, "template")
                self.db.add_log(self.job_id, "github", "Cloning template...")
                git.Repo.clone_from(template_git_url, template_path)

                # Clone new empty repo
                new_repo_url = f"https://{os.environ['GITHUB_TOKEN']}@github.com/{self.repo.full_name}.git"
                new_repo_path = os.path.join(temp_dir, "new-repo")
                self.db.add_log(self.job_id, "github", "Setting up new repo...")
                new_repo = git.Repo.clone_from(new_repo_url, new_repo_path)

                # Configure git user
                configure_git_user_for_repo(new_repo)

                # Copy template files to new repo
                self.db.add_log(self.job_id, "github", "Copying template files...")
                for item in os.listdir(template_path):
                    if item != ".git":
                        src = os.path.join(template_path, item)
                        dst = os.path.join(new_repo_path, item)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)

                # Commit and push template files
                self.db.add_log(self.job_id, "github", "Pushing initial commit...")
                new_repo.git.add(A=True)
                new_repo.index.commit("Initial commit from template")
                new_repo.git.push("origin", "main")
            print("exit temp dir, copying and push is done")
        except Exception as e:
            self.db.add_log(self.job_id, "github", f"Error in template copy: {str(e)}")
            # Cleanup repo if it exists
            # if self.repo:
            #     self.repo.delete()
            #     self.db.add_log(self.job_id, "github", "Cleaned up failed repo")
            raise
