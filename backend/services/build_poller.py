from backend.integrations.db import Database
from backend.services.vercel_build_service import VercelBuildService

class BuildPoller:
    def __init__(self, project_id: str, build_id: str):
        self.project_id = project_id
        self.build_id = build_id
        self.db = Database()
        self.vercel_service = VercelBuildService(project_id)

    def start_polling(self) -> dict:
        """
        Start polling for build status updates
        Now a thin wrapper around VercelBuildService's poll_build_status
        """
        print(f'[BuildPoller] Starting build polling for {self.build_id}')
        result = self.vercel_service.poll_build_status(build_id=self.build_id)
        print(f'[BuildPoller] Completed build polling for {self.build_id}: {result}')
        return result
