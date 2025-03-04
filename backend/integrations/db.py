import os
from typing import Optional
import uuid
from datetime import datetime


class Database:
    def __init__(self):
        from supabase import create_client

        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_API_KEY")
        if not url or not key:
            raise RuntimeError(
                "Supabase credentials not configured. "
                "Ensure you've added the supabase-secret to your Modal function."
            )

        self.client = create_client(url, key)

    def create_project(
        self, fid_owner: int, repo_url: str, frontend_url: str, data: dict = {}
    ) -> str:
        """Create a new project record"""
        project_id = str(uuid.uuid4())
        print(
            f"Creating project: fid={fid_owner}, repo={repo_url}, frontend={
                frontend_url
            }"
        )
        self.client.table("projects").insert(
            {
                "id": project_id,
                "created_at": datetime.utcnow().isoformat(),
                "fid_owner": fid_owner,
                "repo_url": repo_url,
                "frontend_url": frontend_url,
                "status": "created",
                "data": data,
            }
        ).execute()
        return project_id

    def create_job(
        self, project_id: str, job_type: str, status: str = "pending", data: dict = {}
    ) -> str:
        """Create a new job record"""
        job_id = str(uuid.uuid4())
        print(
            f"Creating job: project={project_id}, type={job_type}, status={
                status
            }, data={data}"
        )
        self.client.table("jobs").insert(
            {
                "id": job_id,
                "created_at": datetime.utcnow().isoformat(),
                "project_id": project_id,
                "type": job_type,
                "status": status,
                "data": data,
            }
        ).execute()
        return job_id

    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None):
        """Update job status"""
        print(
            f"updating job {job_id}: status={status}, error={
                error if error else 'None'
            }"
        )
        new_job = {"status": status}

        existing_job = (
            self.client.table("jobs")
            .select("data")
            .eq("id", job_id)
            .single()
            .execute()
            .data
        )
        existing_data = existing_job.get("data", {}) if existing_job else {}
        if error:
            merged_data = {**existing_data, "error": error}
            new_job["data"] = merged_data

        self.client.table("jobs").update(new_job).eq("id", job_id).execute()

    def add_log(self, job_id: str, source: str, text: str):
        """Add a log entry"""
        print(f"[{source}] {text}")
        self.client.table("logs").insert(
            {
                "id": str(uuid.uuid4()),
                "created_at": datetime.utcnow().isoformat(),
                "job_id": job_id,
                "source": source,
                "text": text,
            }
        ).execute()

    def get_project(self, project_id: str):
        """Get project details"""
        return (
            self.client.table("projects")
            .select("*")
            .eq("id", project_id)
            .single()
            .execute()
            .data
        )

    def get_user_projects(self, fid: int):
        """Get all projects for a user"""
        return (
            self.client.table("projects")
            .select("*")
            .eq("fid_owner", fid)
            .execute()
            .data
        )

    def update_project_vercel_info(self, project_id: str, vercel_info: dict):
        """Update project with Vercel deployment information"""
        print(f"updating project {project_id} with Vercel info: {vercel_info}")
        self.client.table("projects").update(
            {
                "vercel_project_id": vercel_info.get("id"),
            }
        ).eq("id", project_id).execute()

    def update_project_github_repo_id(self, project_id: str, github_repo_id: str):
        """Update project with GitHub repo ID"""
        print(f"updating project {project_id} with GitHub repo ID: {github_repo_id}")
        self.client.table("projects").update(
            {
                "github_repo_id": github_repo_id,
            }
        ).eq("id", project_id).execute()

    def update_project(self, project_id: str, data: dict):
        """Update project with given data"""
        print(f"updating project {project_id} with data: {data}")
        self.client.table("projects").update(data).eq("id", project_id).execute()

    def create_build(
        self, project_id: str, commit_hash: str, status: str, data: dict = {}
    ) -> str:
        """Create a new build record"""
        build_id = str(uuid.uuid4())
        print(
            f"Creating build: project={project_id}, commit={commit_hash}, status={status}"
        )
        self.client.table("builds").insert(
            {
                "id": build_id,
                "created_at": datetime.utcnow().isoformat(),
                "project_id": project_id,
                "commit_hash": commit_hash,
                "status": status,
                "data": data,
            }
        ).execute()
        return build_id

    def update_build_status(
        self, build_id: str, status: str, error: Optional[str] = None
    ):
        """Update build status atomically"""
        print(
            f"Updating build {build_id}: status={status}, error={'None' if not error else error}"
        )
        update_data = {"status": status}

        if error:
            existing_data = (
                self.client.table("builds")
                .select("data")
                .eq("id", build_id)
                .single()
                .execute()
                .data.get("data", {})
            )
            update_data["data"] = {**existing_data, "error": error}

        self.client.table("builds").update(update_data).eq("id", build_id).execute()

    def add_build_log(self, build_id: str, source: str, text: str):
        """Add a build log entry"""
        print(f"[Build {build_id}][{source}] {text}")
        self.client.table("build_logs").insert(
            {
                "id": str(uuid.uuid4()),
                "build_id": build_id,
                "source": source,
                "text": text,
            }
        ).execute()

    def get_build_by_id(self, build_id: str):
        """Get build record by ID"""
        return (
            self.client.table("builds")
            .select("*")
            .eq("id", build_id)
            .maybe_single()
            .execute()
            .data
        )

    def get_builds_by_project(self, project_id: str):
        """Get all builds for a project ordered by creation time (newest first)"""
        return (
            self.client.table("builds")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def get_build_by_commit(self, project_id: str, commit_hash: str):
        """Get build record by commit hash"""
        result = (
            self.client.table("builds")
            .select("*")
            .eq("project_id", project_id)
            .eq("commit_hash", commit_hash)
            .maybe_single()
            .execute()
        )
        return result.data if result else None

    def update_build(self, build_id: str, update_data: dict):
        """Update build"""
        print(f"[db] Updating build {build_id} with data: {update_data}")
        self.client.table("builds").update(update_data).eq("id", build_id).execute()
