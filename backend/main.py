from backend.types import UserContext
import modal

from backend.modal import app, volumes, all_secrets, db_secrets
from backend import config
from backend.integrations.db import Database


@app.function(secrets=db_secrets)
@modal.web_endpoint(label="create-project-webhook", method="POST", docs=True)
def create_project_webhook(data: dict) -> dict:
    """
    Webhook that creates a project record and triggers background job.
    """
    print(f"received webhook data: {data}")
    required_fields = ["prompt", "user_context"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    db = Database()
    project_id = db.create_project(
        fid_owner=data["user_context"]["fid"],
        repo_url="",
        frontend_url="",
    )

    job_id = db.create_job(project_id=project_id, job_type="setup_project", data=data)

    create_project_data = {
        "project_id": project_id,
        "job_id": job_id,
        "data": data,
    }
    create_project.spawn(create_project_data)
    return {
        "status": "pending",
        "project_id": project_id,
        "job_id": job_id,
        "message": "Project setup started",
    }


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=all_secrets,
    name=config.MODAL_CREATE_PROJECT_FUNCTION_NAME,
)
def create_project(data: dict) -> dict:
    from backend.services.project_service import ProjectService

    project_id = data["project_id"]
    job_id = data["job_id"]
    user_payload = data["data"]

    ProjectService(project_id, job_id, user_payload).run()


@app.function(secrets=db_secrets)
@modal.web_endpoint(label="update-code-webhook", method="POST", docs=True)
def update_code_webhook(data: dict) -> dict:
    """
    Webhook that updates the code for a project.
    """
    print(f"received webhook data: {data}")
    required_fields = ["prompt", "project_id", "user_context"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    db = Database()
    job_id = db.create_job(
        project_id=data["project_id"], job_type="update_code", data=data
    )

    # Create an async function call without waiting for results
    update_code.spawn(data)

    return {
        "status": "pending",
        "project_id": data["project_id"],
        "job_id": job_id,
        "message": "Code update started",
    }


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=all_secrets,
    name=config.MODAL_UPDATE_CODE_FUNCTION_NAME,
)
def update_code(data: dict) -> dict:
    from backend.services.code_service import CodeService

    project_id = data["project_id"]
    prompt = data["prompt"]
    user_context: UserContext = data["user_context"]

    db = Database()

    job_id = db.create_job(project_id=project_id, job_type="update_code", data=data)

    code_service = CodeService(project_id, job_id, user_context)
    code_service.run(prompt)

    return "Code update completed"
