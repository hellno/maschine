from backend.types import UserContext
import modal

from backend.modal import app, volumes, all_secrets, db_secrets
from backend.services.deploy_project_service import DeployProjectService
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
    from backend.services.create_project_service import CreateProjectService

    project_id = data["project_id"]
    job_id = data["job_id"]
    user_payload = data["data"]

    CreateProjectService(project_id, job_id, user_payload).setup_core_infrastructure()
    return {"status": "core_setup_complete"}


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
    data["job_id"] = job_id

    update_code.spawn(data)

    return {
        "status": "pending",
        "project_id": data["project_id"],
        "job_id": job_id,
        "message": "Code update started",
    }


@app.function(secrets=db_secrets)
@modal.web_endpoint(label="deploy-project-webhook", method="POST", docs=True)
def deploy_project_webhook(data: dict) -> dict:
    """
    Webhook that triggers final deployment steps for a project.
    """
    print(f"received webhook data: {data}")
    required_fields = ["project_id", "user_context"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    db = Database()
    job_id = db.create_job(
        project_id=data["project_id"], job_type="final_deploy", data=data
    )

    deploy_project.spawn(
        {
            "project_id": data["project_id"],
            "job_id": job_id,
            "user_context": data["user_context"],
        }
    )

    return {
        "status": "pending",
        "project_id": data["project_id"],
        "job_id": job_id,
        "message": "Project deployment started",
    }


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=all_secrets,
    name=config.MODAL_DEPLOY_PROJECT_FUNCTION_NAME,
)
def deploy_project(data: dict) -> dict:
    """Handle final deployment steps"""
    project_id = data["project_id"]
    job_id = data["job_id"]
    user_context = data["user_context"]

    DeployProjectService(project_id, job_id, user_context).run()
    return {"status": "deployment_complete"}


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=all_secrets,
    name=config.MODAL_UPDATE_CODE_FUNCTION_NAME,
)
def update_code(data: dict) -> dict:
    from backend.services.code_service import CodeService

    project_id = data["project_id"]
    job_id = data["job_id"]
    prompt = data["prompt"]
    user_context: UserContext = data["user_context"]

    code_service = CodeService(project_id, job_id, user_context)
    code_service.run(prompt)

    return "Code update completed"
