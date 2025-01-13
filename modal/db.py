from supabase import create_client
import os
from typing import Optional, List
import uuid
from datetime import datetime

class Database:
    def __init__(self):
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_API_KEY"]
        self.client = create_client(url, key)

    def create_project(self, fid_owner: int, repo_url: str, frontend_url: str) -> str:
        """Create a new project record"""
        project_id = str(uuid.uuid4())
        self.client.table('projects').insert({
            'id': project_id,
            'created_at': datetime.utcnow().isoformat(),
            'fid_owner': fid_owner,
            'repo_url': repo_url,
            'frontend_url': frontend_url
        }).execute()
        return project_id

    def create_job(self, project_id: str, job_type: str, status: str = 'pending') -> str:
        """Create a new job record"""
        job_id = str(uuid.uuid4())
        self.client.table('jobs').insert({
            'id': job_id,
            'created_at': datetime.utcnow().isoformat(),
            'project_id': project_id,
            'type': job_type,
            'status': status,
            'data': {}
        }).execute()
        return job_id

    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None):
        """Update job status"""
        data = {'status': status}
        if error:
            data['data'] = {'error': error}
        self.client.table('jobs').update(data).eq('id', job_id).execute()

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
        return self.client.table('projects').select('*').eq('id', project_id).single().execute()

    def get_user_projects(self, fid: int):
        """Get all projects for a user"""
        return self.client.table('projects').select('*').eq('fid_owner', fid).execute()
