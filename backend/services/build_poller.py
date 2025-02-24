import time
from typing import Optional, Dict
from backend.integrations.db import Database
from backend.services.vercel_build_service import VercelBuildService

class BuildPoller:
    def __init__(self, project_id: str, build_id: str):
        self.project_id = project_id
        self.build_id = build_id
        self.db = Database()
        self.vercel_service = VercelBuildService(project_id)
        
        # Configure polling parameters
        self.max_attempts = 30  # 5 minutes with 10s interval
        self.poll_interval = 10  # seconds
        
    def start_polling(self) -> Dict:
        """
        Start polling for build status updates
        Returns final build status or error
        """
        attempts = 0
        
        while attempts < self.max_attempts:
            try:
                # Get current build record
                build = self.db.get_build_by_commit(self.project_id, self.build_id)
                if not build:
                    return {"error": "Build not found"}
                
                # Get Vercel deployment ID
                vercel_id = build.get("vercel_deployment_id")
                if not vercel_id:
                    self.db.add_build_log(
                        self.build_id,
                        "poller",
                        "No Vercel deployment ID found"
                    )
                    return {"error": "No Vercel deployment ID"}
                
                # Get deployment status
                deployment = self.vercel_service.get_deployment_by_id(vercel_id)
                if "error" in deployment:
                    self.db.add_build_log(
                        self.build_id,
                        "poller",
                        f"Failed to get deployment: {deployment['error']}"
                    )
                    return deployment
                
                # Parse and update status
                status = self._parse_deployment_status(deployment)
                self.db.update_build_status(self.build_id, status["status"])
                
                # Add status log
                self.db.add_build_log(
                    self.build_id,
                    "poller",
                    f"Build status: {status['status']}"
                )
                
                # Check if we've reached a terminal state
                if status["status"] in ["success", "failed"]:
                    return status
                
            except Exception as e:
                self.db.add_build_log(
                    self.build_id,
                    "poller",
                    f"Polling error: {str(e)}"
                )
            
            attempts += 1
            time.sleep(self.poll_interval)
        
        # If we get here, polling timed out
        timeout_status = {"status": "failed", "error": "Polling timeout"}
        self.db.update_build_status(
            self.build_id,
            "failed",
            "Build status polling timed out"
        )
        return timeout_status
    
    def _parse_deployment_status(self, deployment: Dict) -> Dict:
        """Convert Vercel deployment status to our format"""
        state = deployment.get("state", "").upper()
        
        if state == "READY":
            return {"status": "success"}
        elif state == "ERROR":
            return {
                "status": "failed",
                "error": deployment.get("errorMessage", "Unknown error")
            }
        elif state in ["BUILDING", "INITIALIZING"]:
            return {"status": "building"}
        elif state == "QUEUED":
            return {"status": "queued"}
        else:
            return {"status": "unknown"}
