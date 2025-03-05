#!/usr/bin/env python3

# run with
# PYTHONPATH=$PYTHONPATH:. python scripts/update_docs_index.py

"""
Script to fix failed setup project jobs by applying initial customization
and updating database states.
"""

import sys
import argparse
import json
from dotenv import load_dotenv
from typing import Optional, Dict
from backend.integrations.db import Database
from backend.services.setup_project_service import SetupProjectService
from backend.services.code_service import CodeService
import re
from backend.services.prompts import RETRY_IMPLEMENT_TODO_LIST_PROMPT

load_dotenv()

def find_setup_job(db: Database, project_id: Optional[str], project_name: Optional[str]) -> tuple[Optional[str], Optional[Dict], Optional[str]]:
    """
    Find the setup_project job for the specified project.

    Args:
        db: Database instance
        project_id: The project ID to lookup
        project_name: The project name to lookup

    Returns:
        Tuple of (job_id, job_data, project_id) or (None, None, None) if not found
    """
    if not project_id and not project_name:
        raise ValueError("Either project_id or project_name must be provided")

    try:
        # Query for the setup_project job using Supabase client
        query, value = '', ''
        if project_id:
            query = "project_id"
            value = project_id
        elif project_name:
            query = "projects.name"
            value = project_name
        print(f'Looking for setup job with query {query} and value {value}')
        result = db.client.from_("jobs") \
            .select("*, projects!inner(name)") \
            .eq(query, value) \
            .limit(1) \
            .execute()

        if result.data and len(result.data) > 0:
            job = result.data[0]
            job_id = job["id"]
            job_data = job.get("data", {})
            project_id = job["project_id"]

            # Parse job_data if it's a string
            if isinstance(job_data, str):
                try:
                    job_data = json.loads(job_data)
                except json.JSONDecodeError:
                    job_data = {}

            return job_id, job_data, project_id

        return None, None, None
    except Exception as e:
        print(f"Error querying for setup job: {str(e)}")
        return None, None, None

def keep_building_project(project_id: Optional[str], project_name: Optional[str]):
    """
    Fix a setup project job by applying initial customization and updating DB states.

    Args:
        project_id: The ID of the project to fix

    Returns:
        True if successful, False otherwise
    """
    try:
        db = Database()
        print(f'Looking for setup job for project id {project_id} or name {project_name}')
        job_id, job_data, project_id = find_setup_job(db, project_id, project_name)
        print(f'got setup job {job_id} for project {project_id}')

        if not job_id or not job_data or not project_id:
            print(f"Error: No setup_project job found for project id {project_id} or name {project_name}")
            return False

        print(f"Found setup job {job_id} for project {project_id} with data {job_data}")

        # Initialize the SetupProjectService
        setup_service = SetupProjectService(
            project_id=project_id,
            job_id=job_id,
            data=job_data
        )
        code_service = CodeService(project_id, job_id, setup_service.user_context, manual_sandbox_termination=True)
        if not code_service.repo_dir:
            print(f"Error: No repository directory found for project {project_id}")
            return False
        code_service._create_sandbox(repo_dir=code_service.repo_dir)

        MAX_ITERATAIONS = 5
        for iteration in range(MAX_ITERATAIONS):
            try:
                todo_content = code_service._read_file_from_sandbox("todo.md")
                open_todo_count = len(re.findall(r'- \[ \]', todo_content))
                solved_todo_count = len(re.findall(r'- \[x\]', todo_content))
                print(f'open todos: {open_todo_count}, solved todos: {solved_todo_count}')
                if open_todo_count == 0 and solved_todo_count > 0:
                    print(f"no open todos found after iteration {iteration+1} -> stop building")
                    break

                print(f"retrying implementation (iteration {iteration+1})")
                result = code_service.run(
                    RETRY_IMPLEMENT_TODO_LIST_PROMPT,
                    auto_enhance_context=False
                )
                print('result', result)
            except Exception as e:
                print(f"Retry iteration {iteration+1} failed: {str(e)}")
                continue

    except Exception as e:
        error_msg = f"Error during fix process: {str(e)}"
        print(error_msg)
        return False

def main():
    parser = argparse.ArgumentParser(description="Keep building project from todo.md")
    parser.add_argument("--project-id", help="The ID of the project to keep building")
    parser.add_argument("--project-name", help="The name of the project to keep building")
    args = parser.parse_args()

    success = keep_building_project(args.project_id, args.project_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
