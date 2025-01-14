import modal
import sys
from pathlib import Path
import os
import requests
from db import Database
from openai import OpenAI
from github import Github
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import base64
import re
import git
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

# Organization constants
GITHUB_ORG_NAME = "frameception-v2"

env_vars = {
    "PATH": "/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
}

github_repos = modal.Volume.from_name(
    "frameception-github-repos", create_if_missing=True)
volumes = {"/github-repos": github_repos}

image = modal.Image.debian_slim(python_version="3.12") \
    .apt_install("git") \
    .env(env_vars) \
    .pip_install(
        "fastapi[standard]",
        "aider-chat",
        "aider-install",
        "GitPython",
        "PyGithub",
        "requests",
        "openai",
        "supabase",
        "eth-account"
).run_commands("aider-install")
app = modal.App(name="frameception", image=image)


def sanitize_project_name(name: str) -> str:
    """Sanitize project name for Vercel compatibility"""
    import re
    sanitized = re.sub(r'[^a-z0-9._-]', '-', name.lower())
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized[:100].strip('-')
    return sanitized or 'new-frame-project'


def generate_random_secret() -> str:
    """Generate a random secret for NextAuth"""
    return base64.b64encode(os.urandom(32)).decode('utf-8')


def verify_github_setup(gh: Github, job_id: str, db: Database) -> None:
    """Verify GitHub token and organization access"""
    required_scopes = ['repo', 'admin:org']

    try:
        # Check authentication
        user = gh.get_user()
        print(f"Authenticated as GitHub user: {user.login}")

        # Check organization access
        org = gh.get_organization(GITHUB_ORG_NAME)
        db.add_log(job_id, "github", f"Successfully accessed organization: {
            GITHUB_ORG_NAME}")

    except Exception as e:
        raise Exception(f"GitHub setup verification failed: {str(e)}")


# @app.local_entrypoint()
# def main(num_iterations: int = 200):
#     """Run the function in different modes and aggregate results.

#     Args:
#         num_iterations: Number of parallel iterations to run (default: 200)
#     """
#     # run the function locally
#     print("Local result:", f.local(1000))

#     # run the function remotely on Modal
#     print("Remote result:", f.remote(1000))

#     # run the function in parallel and remotely on Modal
#     total = 0
#     for ret in f.map(range(num_iterations)):
#         total += ret

#     print(f"Total from {num_iterations} parallel executions:", total)

@app.function()
@modal.web_endpoint(label="update-code", method="POST", docs=True)
def update_code_webhook(data: dict) -> str:
    """Webhook endpoint to trigger code update for a repository"""
    if not data.get("projectId") or not data.get("prompt"):
        return "Please provide projectId and prompt in the request body", 400

    print(f"Received updated code webhook request {data}")
    update_code.remote(data)
    return "Code update initiated"


@app.function(
    volumes=volumes,
    timeout=600,  # 10 mins
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret")
    ]
)
def update_code(data: dict) -> str:
    import git
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    import os

    print('Received updated code request:', data)
    db = Database()
    job_id = db.create_job(data.get("projectId"),
                           job_type="update_code",
                           data=data)
    project = db.get_project(data.get("projectId"))
    if not project:
        return "Project not found", 404
    print(f"project found: {project}")
    repo_path = project.get("repo_url").replace("https://github.com/", "")
    print(f"Processing repository: {repo_path} and got project {project}")
    db.add_log(job_id, "backend",
               f"Starting code update for repo: {repo_path}")

    if not data.get("prompt"):
        return "Please provide a prompt in the request body", 400

    repo_url = f"https://{os.environ["GITHUB_TOKEN"]
                          }@github.com/{repo_path}.git"
    repo_dir = f"/github-repos/{repo_path}"

    print(f"Processing repository: {repo_path}, saving to {repo_dir}")
    try:
        is_repo_stored_locally = os.path.exists(repo_dir)
        repo = None
        if not is_repo_stored_locally:
            repo = git.Repo.clone_from(repo_url, repo_dir)
        else:
            repo = git.Repo(repo_dir)
            repo.remotes.origin.pull()

        repo.config_writer().set_value("user", "name", "hellno").release()
        repo.config_writer().set_value(
            "user", "email", "686075+hellno@users.noreply.github.com.").release()
        fnames = [f"{repo.working_tree_dir}/{fname}"
                  for fname in [
            "src/components/Frame.tsx",
            "src/lib/constants.ts"
        ]
        ]
        io = InputOutput(yes=True, root=repo.working_tree_dir)
        model = Model(
            model="deepseek/deepseek-coder",
            weak_model=None,
            editor_model="deepseek/deepseek-coder"
        )
        coder = Coder.create(
            main_model=model,
            fnames=fnames,
            io=io
        )

        prompt = data["prompt"]
        print(f'Prompt for aider: {prompt}\nmodel: {model}\nfnames: {
              fnames}\ncwd: {repo.working_tree_dir}\ncoder: {coder}')
        # Run the prompt through aider
        result = coder.run(prompt)
        # Commit changes if any were made

        repo.git.push()
        db.update_job_status(job_id, "completed")
        volumes["/github-repos"].commit()
        return f"Successfully ran prompt for repo {repo_path} in project {projectId}"
    except Exception as e:
        error_msg = f"Error processing repository: {str(e)}"
        db.add_log(job_id, "backend", error_msg)
        db.update_job_status(job_id, "failed", str(e))
        return error_msg


@app.function(
    secrets=[
        modal.Secret.from_name("supabase-secret")
    ]
)
@modal.web_endpoint(label="create-frame-project-webhook", method="POST", docs=True)
def create_frame_project_webhook(data: dict) -> dict:
    """Quick webhook endpoint that creates project record and triggers background job"""
    import os
    from github import Github
    import requests
    from openai import OpenAI
    import uuid
    import base64
    import time

    db = Database()

    try:
        required_fields = ["prompt", "description", "fid", "username"]
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, 400

        project_id = db.create_project(
            fid_owner=int(data["fid"]),
            repo_url="",
            frontend_url=""
        )

        # Create job to track progress
        job_id = db.create_job(project_id, job_type="setup_project", data=data)
        db.add_log(job_id, "backend", "Frame initiated")

        # Trigger background job
        setup_frame_project.spawn(data, project_id, job_id)

        # Return immediately with project and job IDs
        return {
            "status": "pending",
            "projectId": project_id,
            "jobId": job_id,
            "message": "Project creation started"
        }

    except Exception as e:
        error_msg = f"Error initiating project creation: {str(e)}"
        return {"error": error_msg}, 500


@app.function(
    secrets=[
        modal.Secret.from_name("farcaster-secret")
    ]
)
def generate_domain_association(domain: str) -> dict:
    """Generate a domain association signature for Farcaster frames.

    Args:
        domain: The domain to generate association for (without http/https)

    Returns:
        Dict containing compact and JSON formats of the signed domain association

    Raises:
        ValueError: If domain is invalid or starts with http/https
    """
    import os
    from eth_account import Account
    from eth_account.messages import encode_defunct
    import json
    import base64
    import re

    try:
        # Validate domain format
        if domain.lower().startswith(('http://', 'https://')):
            raise ValueError(
                "Domain should not include http:// or https:// prefix")

        # Basic domain format validation
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, domain):
            raise ValueError("Invalid domain format")

        # Get environment variables
        fid = int(os.environ.get("FID", 0))
        custody_address = os.environ.get("CUSTODY_ADDRESS", "")
        private_key = os.environ.get("PRIVATE_KEY", "")

        # Validate configuration
        if not all([fid, custody_address, private_key]):
            raise ValueError("Server configuration incomplete")

        # Create header and payload
        header = {
            "fid": fid,
            "type": "custody",
            "key": custody_address
        }

        payload = {
            "domain": domain
        }

        # Encode components to base64url
        def to_base64url(data: dict) -> str:
            json_str = json.dumps(data)
            bytes_data = json_str.encode('utf-8')
            base64_str = base64.urlsafe_b64encode(bytes_data).decode('utf-8')
            return base64_str.rstrip('=')  # Remove padding

        encoded_header = to_base64url(header)
        encoded_payload = to_base64url(payload)

        # Create message to sign
        message = f"{encoded_header}.{encoded_payload}"

        # Create signable message using encode_defunct
        signable_message = encode_defunct(text=message)

        # Sign message using ethereum account
        signed_message = Account.sign_message(signable_message, private_key)

        # Get the signature bytes and encode to base64url
        encoded_signature = base64.urlsafe_b64encode(
            signed_message.signature).decode('utf-8').rstrip('=')

        # Create response formats
        compact_jfs = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
        json_jfs = {
            "header": encoded_header,
            "payload": encoded_payload,
            "signature": encoded_signature
        }

        return {
            "compact": compact_jfs,
            "json": json_jfs
        }

    except Exception as e:
        raise Exception(f"Failed to generate domain association: {str(e)}")


@app.function(
    volumes=volumes,
    timeout=3600,  # 1 hour
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret")
    ]
)
def setup_frame_project(data: dict, project_id: str, job_id: str) -> None:
    """Background job that handles the full project setup"""
    import os
    from github import Github
    import requests
    from openai import OpenAI
    import uuid
    import base64
    import time

    def validate_input(data: dict) -> None:
        required_fields = ["prompt", "description", "fid", "username"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def generate_project_name(prompt: str, deepseek: OpenAI) -> str:
        """Generate project name using Deepseek AI"""
        name_response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Generate a concise, aspirational project name. Only respond with the name."},
                {"role": "user", "content": f"Generate a short project name based on: {prompt}"}
            ],
            temperature=2,
            max_tokens=25
        )
        return name_response.choices[0].message.content.strip()

    def setup_github_repo(gh: Github, sanitized_name: str, description: str) -> object:
        """Create and setup GitHub repository with template contents"""
        import tempfile
        import shutil
        import git

        db = Database()

        try:
            # Get organization
            org = gh.get_organization(GITHUB_ORG_NAME)
            db.add_log(job_id, "github", f"Connected to organization: {
                       GITHUB_ORG_NAME}")

            # Check if repo exists
            try:
                existing_repo = org.get_repo(sanitized_name)
                if existing_repo:
                    raise Exception(
                        f"Repository '{sanitized_name}' already exists")
            except Exception as e:
                if "Not Found" not in str(e):
                    raise

            # Create new repo
            repo = org.create_repo(
                name=sanitized_name,
                description=description,
                private=False
            )
            db.add_log(job_id, "github",
                       f"Created repository: {repo.html_url}")

            # Create temporary directory for local operations
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Clone template repository
                    template_url = "https://github.com/hellno/farcaster-frames-template.git"
                    template_path = os.path.join(temp_dir, "template")
                    git.Repo.clone_from(template_url, template_path)
                    db.add_log(job_id, "github", "Cloned template repository")

                    # Clone new repository
                    new_repo_url = f"https://{
                        os.environ['GITHUB_TOKEN']}@github.com/{repo.full_name}.git"
                    new_repo_path = os.path.join(temp_dir, "new-repo")
                    new_repo = git.Repo.clone_from(new_repo_url, new_repo_path)
                    db.add_log(job_id, "github", "Cloned new repository")

                    # Configure git user
                    new_repo.config_writer().set_value("user", "name", "hellno").release()
                    new_repo.config_writer().set_value(
                        "user", "email", "686075+hellno@users.noreply.github.com").release()

                    # Copy template contents to new repo
                    for item in os.listdir(template_path):
                        if item != '.git':  # Skip .git directory
                            src = os.path.join(template_path, item)
                            dst = os.path.join(new_repo_path, item)
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)

                    # Stage all files
                    new_repo.git.add(A=True)

                    # Commit all changes
                    new_repo.index.commit("Initial bulk copy from template")

                    # Push to GitHub
                    new_repo.git.push('origin', 'main')

                    db.add_log(job_id, "github",
                               "Successfully copied template files")
                    return repo

                except Exception as e:
                    raise Exception(
                        f"Failed during repository setup: {str(e)}")

        except Exception as e:
            db.add_log(job_id, "github",
                       f"Error in setup_github_repo: {str(e)}")
            raise

    def create_vercel_deployment(sanitized_name: str, repo: object) -> tuple:
        """Create Vercel project and trigger deployment"""
        vercel_headers = {
            "Authorization": f"Bearer {os.environ['VERCEL_TOKEN']}",
            "Content-Type": "application/json"
        }

        # First create the project
        project_data = {
            "name": sanitized_name,
            "framework": "nextjs",
            "gitRepository": {
                "type": "github",
                "repo": repo.full_name
            },
            "installCommand": "yarn install",
            "buildCommand": "yarn build",
            "outputDirectory": ".next"
        }

        vercel_project = requests.post(
            f"https://api.vercel.com/v9/projects?teamId={
                os.environ['VERCEL_TEAM_ID']}",
            headers=vercel_headers,
            json=project_data
        ).json()

        if "error" in vercel_project:
            raise Exception(f"Failed to create Vercel project: {
                            vercel_project['error']}")

        print(f"Creating Vercel project: {project_data}")
        print(f"Vercel project created: {vercel_project}")

        # Now add the environment variables
        env_vars = [
            {
                "key": "NEXTAUTH_SECRET",
                "value": generate_random_secret(),
                "type": "encrypted",
                "target": ["production", "preview", "development"]
            },
            {
                "key": "KV_REST_API_URL",
                "value": os.environ["KV_REST_API_URL"],
                "type": "encrypted",
                "target": ["production", "preview", "development"]
            },
            {
                "key": "KV_REST_API_TOKEN",
                "value": os.environ["KV_REST_API_TOKEN"],
                "type": "encrypted",
                "target": ["production", "preview", "development"]
            }
        ]

        # Add each environment variable
        for env_var in env_vars:
            env_response = requests.post(
                f"https://api.vercel.com/v9/projects/{
                    sanitized_name}/env?teamId={os.environ['VERCEL_TEAM_ID']}",
                headers=vercel_headers,
                json=env_var
            ).json()

            if "error" in env_response:
                print(f"Warning: Failed to set env var {
                      env_var['key']}: {env_response['error']}")

        # Create deployment
        deployment = requests.post(
            f"https://api.vercel.com/v13/deployments?teamId={
                os.environ['VERCEL_TEAM_ID']}",
            headers=vercel_headers,
            json={
                "name": sanitized_name,
                "gitSource": {
                    "type": "github",
                    "repoId": str(repo.id),
                    "ref": "main"
                }
            }
        ).json()

        if "error" in deployment:
            raise Exception(f"Failed to create deployment: {
                            deployment['error']}")

        return deployment

    db = Database()

    try:
        # Initialize and verify GitHub client
        try:
            gh = Github(os.environ["GITHUB_TOKEN"])
            verify_github_setup(gh, job_id, db)
        except Exception as e:
            error_msg = f"GitHub setup failed: {str(e)}"
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", error_msg)
            return

        # Initialize OpenAI client
        deepseek = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )

        # Generate and sanitize project name
        project_name = generate_project_name(data["prompt"], deepseek)
        username = data["username"]
        sanitized_name = f'{username}-{sanitize_project_name(project_name)}'

        # Setup GitHub repository
        db.add_log(job_id, "github",
                   f"Creating GitHub repository: {sanitized_name}")
        repo = setup_github_repo(gh, sanitized_name, data["description"])
        db.add_log(job_id, "github", f"Created GitHub repo: {repo.html_url}")

        # Create Vercel deployment
        db.add_log(job_id, "vercel", "Creating Vercel project")
        deployment = create_vercel_deployment(sanitized_name, repo)
        # Update project with final URLs
        frontend_url = f"https://{deployment['url']}"
        db.client.table('projects').update({
            'repo_url': repo.html_url,
            'frontend_url': frontend_url
        }).eq('id', project_id).execute()

        db.add_log(job_id, "vercel", f"Deployment created at: {frontend_url}")

        try:
            # Extract repo path from repo.full_name
            repo_path = repo.full_name  # Format: "frameception-v2/repo-name"

            # First code update
            code_update_response = update_code.remote({
                "projectId": project_id,
                "repo_path": repo_path,
                "prompt": data["prompt"],
                "job_type": "update_code"
            })
            db.add_log(job_id, "backend", f"Initial code update completed: {
                       code_update_response}")

            print("Starting post-deployment setup with deployment data", deployment)
            # Generate domain association
            domain = deployment['url']
            if domain.startswith('https://'):
                domain = domain[8:]
            domain_assoc = generate_domain_association.remote(domain)
            print("Generated domain association", domain_assoc)
            db.add_log(job_id, "backend", "Generated domain association")

            # Create prompt for domain association update
            update_prompt = f"""
            Update the file src/app/.well-known/farcaster.json/route.ts to return the following domain association:

            ```typescript
            import {{ NextResponse }} from "next/server";

            export async function GET() {{
                return NextResponse.json({{
                    headers: {domain_assoc['json']['header']},
                    payload: {domain_assoc['json']['payload']},
                    signature: {domain_assoc['json']['signature']}
                }});
            }}
            ```
            """

            # Update domain association
            domain_update_response = update_code.remote({
                "projectId": project_id,
                "repo_path": repo_path,
                "prompt": update_prompt,
                "job_type": "update_code"
            })
            db.add_log(job_id, "backend", f"Domain association update completed: {
                       domain_update_response}")

            db.add_log(job_id, "backend",
                       "All setup steps completed successfully")
            db.update_job_status(job_id, "completed")

        except Exception as e:
            error_msg = f"Error during post-deployment setup: {str(e)}"
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", str(e))

    except Exception as e:
        error_msg = f"Error creating project: {str(e)}"
        db.add_log(job_id, "backend", error_msg)
        db.update_job_status(job_id, "failed", str(e))
