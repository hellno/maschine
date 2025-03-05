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

def find_setup_job(db: Database, project_id: str) -> tuple[Optional[str], Optional[Dict]]:
    """
    Find the setup_project job for the specified project.

    Args:
        db: Database instance
        project_id: The project ID to lookup

    Returns:
        Tuple of (job_id, job_data) or (None, None) if not found
    """
    try:
        # Query for the setup_project job using Supabase client
        result = db.client.from_("jobs") \
            .select("*") \
            .eq("project_id", project_id) \
            .eq("type", "setup_project") \
            .limit(1) \
            .execute()

        if result.data and len(result.data) > 0:
            job = result.data[0]
            job_id = job["id"]
            job_data = job.get("data", {})

            # Parse job_data if it's a string
            if isinstance(job_data, str):
                try:
                    job_data = json.loads(job_data)
                except json.JSONDecodeError:
                    job_data = {}

            return job_id, job_data

        return None, None
    except Exception as e:
        print(f"Error querying for setup job: {str(e)}")
        return None, None

def keep_building_project(project_id: str):
    """
    Fix a setup project job by applying initial customization and updating DB states.

    Args:
        project_id: The ID of the project to fix

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize database connection
        db = Database()

        print(f"Starting fix for project {project_id}")

        # Find the setup_project job for this project
        job_id, job_data = find_setup_job(db, project_id)

        if not job_id or not job_data:
            print(f"Error: No setup_project job found for project {project_id}")
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
    parser.add_argument("project_id", help="The ID of the project to keep building")
    args = parser.parse_args()

    success = keep_building_project(args.project_id)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
