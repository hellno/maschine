import time

from backend.integrations.openrank import get_openrank_score_for_fid
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


@app.function()
@modal.web_endpoint(label="farcaster-webhook", docs=True, method="POST")
def handle_farcaster_webhook(data: dict) -> dict:
    # import os
    # if token.credentials != os.environ["NEYNAR_WEBHOOK_AUTH_TOKEN"]:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect bearer token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    print(f"received handle_farcaster_webhook with data: {data}")
    event_type = data.get("type")
    if event_type == "cast.created":
        text = data.get("data", {}).get("text")
        if text:  # and "build this" in text.lower():
            create_project_from_cast.spawn(data)
            return {"status": "success"}
    return {"status": "ignored"}


def get_prompt_from_conversation(conversation: str) -> str:
    return f"""Build a project based on this social media conversation:
    {conversation}
    """


@app.function(secrets=all_secrets)
def create_project_from_cast(data: dict):
    """Handle cast.created webhooks from Neynar"""
    print("start create_project_from_cast with data: ", data)

    # Post frame reply to original cast
    from backend.integrations.neynar import NeynarPost
    from backend.integrations.neynar import get_conversation_from_cast

    cast = data["data"]
    try:
        conversation = get_conversation_from_cast(cast["hash"])
        print("conversation: ", conversation)
    except Exception as e:
        print("Failed to fetch conversation", e)
        return {"error": "Failed to fetch conversation", "message": f"{str(e)}"}, 500

    user_fid = cast["author"]["fid"]
    openrank_score = get_openrank_score_for_fid(user_fid)
    print("openrank_score: ", openrank_score)
    if openrank_score["percentile"] < 0.9:
        print(
            f"user with fid {user_fid} has openrank score below 0.9, not creating project"
        )
        NeynarPost().reply_to_cast(
            text=f"you must be in the top 10% of users (based on openrank score) to create a project, while we're testing in alpha. {config.FRONTEND_URL}",
            parent_hash=cast["hash"],
            parent_fid=user_fid,
            embeds=[{"url": config.FRONTEND_URL}],
        )

        return {
            "status": "ignored",
            "message": "User does not meet minimum requirements to create a project",
        }

    prompt = get_prompt_from_conversation(conversation)
    user_context = cast["author"]
    payload = dict(
        prompt=prompt,
        user_context=user_context,
    )
    db = Database()
    project_id = db.create_project(
        fid_owner=user_fid,
        repo_url="",
        frontend_url="",
        data={"cast": cast, **payload},
    )
    job_id = db.create_job(
        project_id=project_id,
        job_type="setup_project",
        data=payload,
    )

    create_project.spawn(
        {
            "project_id": project_id,
            "job_id": job_id,
            "data": payload,
        }
    )

    print(
        "spawned create_project function. sleeping for 30 seconds before replying to cast"
    )
    # Wait for initial processing before responding
    time.sleep(30)
    try:
        project = db.get_project(project_id)
        text = f"🚀 Your project is being created! Track status here: {config.FRONTEND_URL}"
        embeds = [
            {
                "url": config.FRONTEND_URL,
            }
        ]

        if project.repo_url:
            text += f"\n🔗 open source repo: {project.repo_url}"
            embeds.append(
                {
                    "url": project.repo_url,
                }
            )

        NeynarPost().reply_to_cast(
            text=text,
            parent_hash=cast["hash"],
            parent_fid=user_fid,
            embeds=embeds,
        )
    except Exception as e:
        print("Failed to reply to cast", e)
        return {"error": "Failed to reply to cast", "message": f"{str(e)}"}, 500

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
