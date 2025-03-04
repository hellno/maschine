#!/usr/bin/env python3
"""
Script to fix failed setup project jobs by applying initial customization
and updating database states.
"""

import sys
import os
import argparse
import json
from typing import Optional, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.integrations.db import Database

# Import the SetupProjectService - adjust the import path if needed
from backend.services.setup_project import SetupProjectService

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
            .order("created_at", {"ascending": False}) \
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

def fix_setup_project(project_id: str) -> bool:
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
        
        if not job_id:
            print(f"Error: No setup_project job found for project {project_id}")
            return False
        
        print(f"Found setup job {job_id} for project {project_id}")
        
        # Log the action
        db.add_log(job_id, "fix_script", "Starting to fix failed setup project job")
        
        # Initialize the SetupProjectService
        setup_service = SetupProjectService(
            project_id=project_id,
            job_id=job_id,
            db=db,
            # Include other parameters that might be required by SetupProjectService
            user_context=job_data.get("user_context", {}),
            # Add other parameters from job_data as needed
        )
        
        # Apply initial customization
        print("Applying initial customization...")
        db.add_log(job_id, "fix_script", "Applying initial customization")
        setup_service._apply_initial_customization()
        
        # Update project status
        print("Updating project status to 'created'...")
        db.add_log(job_id, "fix_script", "Updating project status to 'created'")
        db.update_project(
            project_id,
            {
                "status": "created",
            },
        )
        
        # Update job status
        print("Updating job status to 'completed'...")
        db.add_log(job_id, "fix_script", "Updating job status to 'completed'")
        db.update_job_status(job_id, "completed")
        
        print(f"Successfully fixed setup for project {project_id}")
        db.add_log(job_id, "fix_script", "Successfully fixed setup for project")
        return True
    
    except Exception as e:
        error_msg = f"Error during fix process: {str(e)}"
        print(error_msg)
        if 'job_id' in locals() and 'db' in locals():
            db.add_log(job_id, "fix_script", error_msg)
        return False

def main():
    parser = argparse.ArgumentParser(description="Fix setup project jobs")
    parser.add_argument("project_id", help="The ID of the project to fix")
    args = parser.parse_args()
    
    success = fix_setup_project(args.project_id)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
