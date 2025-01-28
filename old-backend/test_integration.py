import json
import os
import shutil
import git
from backend.utils.github_utils import parse_github_url
import modal

from backend.modal_instance import app, base_image, volumes
from backend.services.project_setup_service import ProjectSetup, ProjectVolume
from backend.config.project_config import ProjectConfig
from backend.integrations.db import Database
from modal import method

TEST_PROJECT_ID = "bf42bd63-2274-4114-8ed0-a03961319242"
TEST_REPO_NAME = "frameception-integration-test"


@app.function(secrets=[modal.Secret.from_dotenv(__file__)])
def setup_integration_test_remote():
    """One-time setup to create test GitHub repo"""
    from github import Github
    import git
    import shutil

    gh = Github(os.environ["GITHUB_TOKEN"])
    org = gh.get_organization(ProjectConfig.GITHUB["ORG_NAME"])

    try:
        template_repo = org.get_repo(TEST_REPO_NAME)
        print(f"Test repo {TEST_REPO_NAME} already exists")
    except Exception:
        template_repo = org.create_repo(
            name=TEST_REPO_NAME,
            description="Frameception integration test repository",
            private=False,
        )
        
        # Update config to match production format
        org_name, repo_name = parse_github_url(template_repo.html_url)
        ProjectConfig.GITHUB["TEMPLATE_REPO"] = f"{org_name}/{repo_name}"
        print(f"Created test repo: {template_repo.html_url}")
    # Initialize with template
    volume = ProjectVolume(TEST_PROJECT_ID)
    if os.path.exists(volume.paths["repo"]):
        shutil.rmtree(volume.paths["repo"])

    repo_dir = volume.paths["repo"]
    repo = git.Repo.clone_from(
        ProjectConfig.GITHUB["TEMPLATE_REPO"],
        repo_dir,
        # depth=1
    )

    # Configure and push to test repo with authentication
    auth_url = f"https://{os.environ['GITHUB_TOKEN']}@github.com/{
        ProjectConfig.GITHUB['ORG_NAME']
    }/{TEST_REPO_NAME}"
    try:
        origin = repo.create_remote("origin", auth_url)
    except git.exc.GitCommandError as e:
        if "already exists" in str(e):
            origin = repo.remote("origin")
            origin.set_url(auth_url)
        else:
            raise
    origin.push(refspec="main:main")

    db = Database()
    db.client.table("projects").upsert(
        {
            "id": TEST_PROJECT_ID,
            "name": "integration_test",
            "fid_owner": 0,
            "repo_url": f"github.com/{ProjectConfig.GITHUB['ORG_NAME']}/{TEST_REPO_NAME}",
        }
    ).execute()

    return template_repo.url


@app.function(secrets=[modal.Secret.from_dotenv(__file__)])
def integration_test_cleanup():
    """Cleanup after each test run"""
    db = Database()

    # Delete test project
    db.client.table("projects").delete().eq("id", TEST_PROJECT_ID).execute()

    # Delete test jobs
    db.client.table("jobs").delete().eq("project_id", TEST_PROJECT_ID).execute()

    # Use ProjectVolume's built-in deletion logic
    volume = ProjectVolume(TEST_PROJECT_ID)
    volume.delete()  # This already handles missing volumes gracefully


class TestProjectSetup(ProjectSetup):  # Inherits from ProjectSetup

    def _setup_github_repository(self):
        """Test-specific GitHub setup with skip handling"""
        if self.data.get("_test_config", {}).get("skip_github"):
            # Create minimal repo for Vercel to reference
            self.repo = git.Repo.init(self.volume.paths["repo"])
            
            # Add mock remote to satisfy Vercel's need for repo URL
            test_repo_url = f"https://github.com/{ProjectConfig.GITHUB['ORG_NAME']}/{TEST_REPO_NAME}"
            self.repo.create_remote("origin", test_repo_url)
            self.repo.git.config("--local", "user.name", "Test User")
            self.repo.git.config("--local", "user.email", "test@frameception.com")
            
            self.db.add_log(self.job_id, "github", "Skipped GitHub setup (test mode)")
            print('🚀 Test mode: Skipped GitHub setup, repo:', self.repo)
            print('self.repo has full_name:', json.loads(self.repo))
            return

        # Parent implementation with test repo URL
        original_template = ProjectConfig.GITHUB["TEMPLATE_REPO"]
        repo_path = self.volume.paths["repo"]

        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)

        # Clone from existing test repo
        self.repo = git.Repo.clone_from(
            f"https://{os.environ['GITHUB_TOKEN']}@github.com/{ProjectConfig.GITHUB['ORG_NAME']}/{TEST_REPO_NAME}",
            repo_path,
            depth=1,
        )

        # Restore original template reference for parent class logic
        ProjectConfig.GITHUB["TEMPLATE_REPO"] = original_template
        self.db.add_log(self.job_id, "github", "Using existing test repo")
        super()._setup_github_repository()  # Call parent for additional setup


@app.local_entrypoint()
def setup_integration_test():
    print("🚀 Creating test repository...")
    setup_integration_test_remote.remote()
    print("✅ Test repository created")


@app.local_entrypoint()
def run_integration_test():
    print("🚀 Starting integration test...")
    run_integration_test_remote.remote()
    print("✅ Integration test completed")


@app.function(secrets=[modal.Secret.from_dotenv(__file__)])
def run_integration_test_remote():
    """Run the integration test suite locally"""
    setup_integration_test_remote.remote()

    print("🚀 Starting integration test...")

    # Test configuration
    test_data = {
        "prompt": "Test frame with existing repo",
        "description": "Integration test frame",
        "userContext": {"fid": 12345, "username": "test-user"},
        "_test_config": {"skip_github": True, "test_repo": TEST_REPO_NAME},
    }

    # Create test job record
    db = Database()
    job_id = db.create_job(
        project_id=TEST_PROJECT_ID, job_type="integration_test", data=test_data
    )

    try:
        # Use spawn pattern matching production code
        project_setup = TestProjectSetup(
            project_id=TEST_PROJECT_ID,
            job_id=job_id,
            data=test_data,
        )
        project_setup.run()

        # Validate results
        project = db.get_project(TEST_PROJECT_ID)
        if not project["vercel_project_id"]:
            raise Exception("Vercel project ID not set")

        # Check for required files
        volume = ProjectVolume(TEST_PROJECT_ID)
        required_files = [
            "package.json",
            "src/components/Frame.tsx",
            "src/app/.well-known/farcaster.json/route.ts",
        ]

        for fpath in required_files:
            full_path = os.path.join(volume.paths["repo"], fpath)
            if not os.path.exists(full_path):
                raise Exception(f"Missing required file: {full_path}")

        print("✅ Integration test passed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        print("🧹 Cleaning up...")
        integration_test_cleanup.remote()
