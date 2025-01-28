import modal

from backend.modal import app, volumes
from backend import config
from backend.integrations.db import Database


@app.function(secrets=[modal.Secret.from_name("supabase-secret")])
@modal.web_endpoint(label="create-project-webhook", method="POST", docs=True)
def create_project_webhook(data: dict) -> dict:
    """
    Webhook that creates a project record and triggers background job.
    """
    print(f"received webhook data: {data}")
    required_fields = ["prompt", "userContext"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    db = Database()
    project_id = db.create_project(
        fid_owner=data["userContext"]["fid"],
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
        "projectId": project_id,
        "jobId": job_id,
        "message": "Project setup started",
    }


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret"),
        modal.Secret.from_name("neynar-secret"),
        modal.Secret.from_name("redis-secret"),
        modal.Secret.from_name("aws-secret"),
    ],
)
def create_project(data: dict) -> dict:
    from backend.services.project_service import ProjectService

    project_id = data["project_id"]
    job_id = data["job_id"]
    user_payload = data["data"]

    ProjectService(project_id, job_id, user_payload).run()


@app.function()
@modal.web_endpoint(label="update-code-webhook", method="POST", docs=True)
def update_code_webhook(data: dict) -> dict:
    """
    Webhook that updates the code for a project.
    """
    print(f"received webhook data: {data}")
    required_fields = ["prompt", "projectId", "userContext"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    db = Database()
    job_id = db.create_job(project_id=data["projectId"], job_type="update_code", data=data)
    
    # Create an async function call without waiting for results
    update_code.spawn(data)

    return {
        "status": "pending",
        "projectId": data["projectId"],
        "jobId": job_id,
        "message": "Code update started",
    }


@app.function(
    volumes=volumes,
    timeout=config.TIMEOUTS["PROJECT_SETUP"],
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret"),
        modal.Secret.from_name("neynar-secret"),
        modal.Secret.from_name("redis-secret"),
        modal.Secret.from_name("aws-secret"),
    ],
)
def update_code(data: dict) -> dict:
    from backend.services.code_service import CodeService

    project_id = data["projectId"]
    prompt = data["prompt"]
    user_context = data["userContext"]

    db = Database()

    job_id = db.create_job(project_id=project_id, job_type="update_code", data=data)

    CodeService(project_id, job_id, prompt, user_context).run()

    return "Code update completed"
