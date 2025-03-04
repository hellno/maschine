import time
from datetime import datetime

from backend.integrations.openrank import get_openrank_score_for_fid
from backend.integrations.vercel_api import VercelApi
from backend.types import UserContext
from backend.utils.sentry import setup_sentry
import modal

from backend.modal import app, volumes, all_secrets, db_secrets
from backend import config
from backend.integrations.db import Database
from typing import Optional


@app.function(secrets=[modal.Secret.from_name("llm-api-keys")])
@modal.web_endpoint(method="POST", label="context-enhancer")
def enhance_context_endpoint(data: dict) -> dict:
    """Enhance a user prompt with relevant technical context"""
    try:
        if "prompt" not in data or not data["prompt"].strip():
            return {"error": "Prompt is required"}, 400

        from backend.services.context_enhancer import CodeContextEnhancer

        enhancer = CodeContextEnhancer()
        context = enhancer.get_relevant_context(data["prompt"])

        return {
            "prompt": data["prompt"],
            "context": context,
        }

    except Exception as e:
        return {"error": f"Context enhancement failed: {str(e)}"}, 500


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

    setup_project_data = {
        "project_id": project_id,
        "job_id": job_id,
        "data": data,
    }
    setup_project.spawn(setup_project_data)
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
        text = data.get("data", {}).get("text", "").lower().strip()
        is_build_command = text.startswith('create') or text.startswith('build')
        if is_build_command:
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
    if openrank_score["percentile"] < 90:
        print(
            f"user with fid {user_fid} has openrank percentile below 90, not creating project. {openrank_score}",
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

    setup_project.spawn(
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
        text = f"""🚀 Your project is being created! Track status here: {config.FRONTEND_URL}
        message @hellno for support"""
        embeds = [
            {
                "url": config.FRONTEND_URL,
            }
        ]

        repo_url = project.get("repo_url")
        if repo_url:
            text += f"\n🔗 open source repo: {repo_url}"
            embeds.append(
                {
                    "url": repo_url,
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
    name=config.MODAL_SETUP_PROJECT_FUNCTION_NAME,
)
def setup_project(data: dict) -> dict:
    from backend.services.setup_project_service import SetupProjectService

    setup_sentry()

    project_id = data["project_id"]
    job_id = data["job_id"]
    user_payload = data["data"]

    SetupProjectService(project_id, job_id, user_payload).run()
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
        project_id=data["project_id"], job_type="deploy_project", data=data
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
    from backend.services.deploy_project_service import DeployProjectService

    setup_sentry()

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
def update_code(data: dict):
    from backend.services.code_service import CodeService

    setup_sentry()

    project_id = data["project_id"]
    job_id = data["job_id"]
    prompt = data["prompt"]
    user_context: UserContext = data["user_context"]

    code_service = CodeService(project_id, job_id, user_context)
    code_service.run(prompt)

    return "Code update completed"


@app.function(secrets=all_secrets, name=f"{config.MODAL_POLL_BUILD_FUNCTION_NAME}_spawn", timeout=600)
def poll_build_status_spawn(project_id: str, build_id: Optional[str] = None, commit_hash: Optional[str] = None):
    """Function to poll build status (for spawning)"""
    try:
        print(f"Polling build status for project {project_id} and build {build_id}")
        from backend.services.vercel_build_service import VercelBuildService
        vercel_service = VercelBuildService(project_id)
        result = vercel_service.poll_build_status(build_id=build_id, commit_hash=commit_hash)
        print('vercel build service polling result: ', result)
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"Error polling build status: {e}")
        return {"status": "error", "message": str(e)}

@app.function(secrets=all_secrets, name=config.MODAL_POLL_BUILD_FUNCTION_NAME, timeout=600)
def poll_build_status(project_id: str, build_id: Optional[str] = None, commit_hash: Optional[str] = None):
    """Function to poll build status (for spawning)"""
    try:
        print(f"Polling build status for project {project_id} and build {build_id}")
        from backend.services.vercel_build_service import VercelBuildService
        vercel_service = VercelBuildService(project_id)
        result = vercel_service.poll_build_status(build_id=build_id, commit_hash=commit_hash)
        print('vercel build service polling result: ', result)
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"Error polling build status: {e}")
        return {"status": "error", "message": str(e)}

@app.function()
@modal.web_endpoint(method="GET", label="poll-build-status-webhook", docs=True)
def poll_build_status_webhook(project_id: str, build_id: str):
    """Endpoint to poll build status"""
    try:
        poll_build_status_spawn.spawn(project_id, build_id)
        datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {"status": "success", "message": "Started polling build status", "datetime": datetime_str}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.function(secrets=all_secrets)
@modal.web_endpoint(method="GET", label="create-vercel-build-webhook", docs=True)
def create_vercel_build_webhook(project_id: str):
    try:
        print(f'creating vercel build webhook for project {project_id}')
        db = Database()
        project = db.get_project(project_id)
        vercel_api = VercelApi(project_id)
        result = vercel_api._trigger_deployment(project.get('name'), project.get('github_repo_id'))
        return {"status": "success", "message": "Started creating vercel build", "result": result}
    except Exception as e:
        print(f"Error creating vercel build webhook: {e}")
        return {"status": "error", "message": str(e)}, 500


@app.function(secrets=all_secrets)
@modal.web_endpoint(method="POST", label="debug-prompt-to-project")
def debug_prompt_to_project(data: dict):
    prompt = data.get('prompt')
    if not prompt:
        return {"status": "error", "message": "prompt is required"}, 400

    from backend.services.context_enhancer import CodeContextEnhancer
    from backend.services.prompts import CREATE_SPEC_PROMPT, CREATE_TASK_PLAN_PROMPT, CREATE_TODO_LIST_PROMPT
    from backend.integrations.llm import send_prompt_to_reasoning_model

    context = CodeContextEnhancer().get_relevant_context(prompt)
    print("got context, now sending prompt to reasoning model")
    create_spec = CREATE_SPEC_PROMPT.format(context=context, prompt=prompt)
    spec_content, spec_reasoning = send_prompt_to_reasoning_model(create_spec)
    print(f"Received spec content: {spec_content}\nReasoning: {spec_reasoning}")

    create_plan = CREATE_TASK_PLAN_PROMPT.format(spec=spec_content)
    plan_content, plan_reasoning = send_prompt_to_reasoning_model(create_plan)
    print(f"Received plan content: {plan_content}\nReasoning: {plan_reasoning}")

    todo = CREATE_TODO_LIST_PROMPT.format(plan=plan_content)
    todo_content, todo_reasoning = send_prompt_to_reasoning_model(todo)
    print(f"Received todo content: {todo_content}\nReasoning: {todo_reasoning}")

    print("All prompts completed successfully")
    results = {
        "context": context,
        "spec": spec_content,
        "plan": plan_content,
        "todo": todo_content
    }
    return {"status": "success", "results": results}, 200

# @app.function(secrets=all_secrets)
# @modal.web_endpoint(method="POST", label="fix-project-setup")
# def fix_project_setup(data: dict):
#     project_id = data.get('project_id')
#     if not project_id:
#         return {"status": "error", "message": "project_id is required"}, 400

#     import json
#     from typing import Optional, Dict
#     from backend.services.setup_project_service import SetupProjectService
#     from backend.integrations.db import Database

#     def find_setup_job(db: Database, project_id: str) -> tuple[Optional[str], Optional[Dict]]:
#         """
#         Find the setup_project job for the specified project.

#         Args:
#             db: Database instance
#             project_id: The project ID to lookup

#         Returns:
#             Tuple of (job_id, job_data) or (None, None) if not found
#         """
#         try:
#             # Query for the setup_project job using Supabase client
#             result = db.client.from_("jobs") \
#                 .select("*") \
#                 .eq("project_id", project_id) \
#                 .eq("type", "setup_project") \
#                 .limit(1) \
#                 .execute()

#             if result.data and len(result.data) > 0:
#                 job = result.data[0]
#                 job_id = job["id"]
#                 job_data = job.get("data", {})

#                 # Parse job_data if it's a string
#                 if isinstance(job_data, str):
#                     try:
#                         job_data = json.loads(job_data)
#                     except json.JSONDecodeError:
#                         job_data = {}

#                 return job_id, job_data

#             return None, None
#         except Exception as e:
#             print(f"Error querying for setup job: {str(e)}")
#             return None, None

#     def fix_setup_project(project_id: str) -> bool:
#         """
#         Fix a setup project job by applying initial customization and updating DB states.

#         Args:
#             project_id: The ID of the project to fix

#         Returns:
#             True if successful, False otherwise
#         """
#         try:
#             # Initialize database connection
#             db = Database()

#             print(f"Starting fix for project {project_id}")

#             # Find the setup_project job for this project
#             job_id, job_data = find_setup_job(db, project_id)

#             if not job_id or not job_data:
#                 print(f"Error: No setup_project job found for project {project_id}")
#                 return False

#             print(f"Found setup job {job_id} for project {project_id} with data {job_data}")

#             # Initialize the SetupProjectService
#             setup_service = SetupProjectService(
#                 project_id=project_id,
#                 job_id=job_id,
#                 data=job_data
#             )

#             # Apply initial customization
#             print("Applying initial customization...")
#             setup_service._apply_initial_customization()

#             # Update project status
#             print("Updating project status to 'created'...")
#             db.update_project(
#                 project_id,
#                 {
#                     "status": "created",
#                 },
#             )

#             # Update job status
#             print("Updating job status to 'completed'...")
#             db.update_job_status(job_id, "completed")

#             print(f"Successfully fixed setup for project {project_id}")
#             return True

#         except Exception as e:
#             error_msg = f"Error during fix process: {str(e)}"
#             print(error_msg)
#             return False

#     fix_setup_project(project_id)
