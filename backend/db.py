from supabase import create_client
import os
from typing import Optional, List
import uuid
from datetime import datetime


class Database:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_API_KEY")
        
        if not url or not key:
            raise RuntimeError(
                "Supabase credentials not configured. "
                "Ensure you've added the supabase-secret to your Modal function."
            )
            
        self.client = create_client(url, key)

    def create_project(self, fid_owner: int, repo_url: str, frontend_url: str) -> str:
        """Create a new project record"""
        project_id = str(uuid.uuid4())
        print(f'Creating project: fid={fid_owner}, repo={
              repo_url}, frontend={frontend_url}')
        self.client.table('projects').insert({
            'id': project_id,
            'created_at': datetime.utcnow().isoformat(),
            'fid_owner': fid_owner,
            'repo_url': repo_url,
            'frontend_url': frontend_url
        }).execute()
        return project_id

    def create_job(self, project_id: str, job_type: str, status: str = 'pending', data: dict = {}) -> str:
        """Create a new job record"""
        job_id = str(uuid.uuid4())
        print(f'Creating job: project={project_id}, type={
              job_type}, status={status}, data={data}')
        self.client.table('jobs').insert({
            'id': job_id,
            'created_at': datetime.utcnow().isoformat(),
            'project_id': project_id,
            'type': job_type,
            'status': status,
            'data': data
        }).execute()
        return job_id

    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None):
        """Update job status"""
        print(f'Updating job {job_id}: status={
              status}, error={error if error else "None"}')
        new_job = {'status': status}

        existing_job = self.client.table('jobs').select(
            'data').eq('id', job_id).single().execute().data
        existing_data = existing_job.get('data', {}) if existing_job else {}
        if error:
            merged_data = {**existing_data, 'error': error}
            new_job['data'] = merged_data

        print('new job:', new_job)
        self.client.table('jobs').update(new_job).eq('id', job_id).execute()

    def add_log(self, job_id: str, source: str, text: str):
        """Add a log entry"""
        print(f'[{source}] {text}')
        self.client.table('logs').insert({
            'id': str(uuid.uuid4()),
            'created_at': datetime.utcnow().isoformat(),
            'job_id': job_id,
            'source': source,
            'text': text
        }).execute()

    def get_project(self, project_id: str):
        """Get project details"""
        return self.client.table('projects').select('*').eq('id', project_id).single().execute().data

    def get_user_projects(self, fid: int):
        """Get all projects for a user"""
        return self.client.table('projects').select('*').eq('fid_owner', fid).execute().data

    def update_project_vercel_info(self, project_id: str, vercel_info: dict):
        """Update project with Vercel deployment information"""
        print(f'Updating project {project_id} with Vercel info: {vercel_info}')
        self.client.table('projects').update({
            'vercel_project_id': vercel_info.get('id'),
        }).eq('id', project_id).execute()
