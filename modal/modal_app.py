import modal
import sys
from pathlib import Path
import os
from db import Database

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


@app.function(volumes=volumes,
              timeout=600,  # 10 mins
              secrets=[
                  modal.Secret.from_name("github-secret"),
                  modal.Secret.from_name("vercel-secret"),
                  modal.Secret.from_name("llm-api-keys"),
                  modal.Secret.from_name("supabase-secret")
              ]
)
@modal.web_endpoint(label="update-code", method="POST", docs=True)
def update_code(data: dict) -> str:
    import git
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    import os

    db = Database()
    # Create a job to track this update
    job_id = db.create_job(data.get("projectId"), job_type="update_code")
    db.add_log(job_id, "backend", f"Starting code update for repo: {
               data.get('repoPath')}")

    if not data.get("repoPath"):
        return "Please provide a repoPath in the request body"

    if not data.get("prompt"):
        return "Please provide a prompt in the request body"

    repo_name = data["repoPath"]

    repo_url = f"https://{os.environ["GITHUB_TOKEN"]
                          }@github.com/{repo_name}.git"
    repo_dir = f"/github-repos/{repo_name}"

    print(f"Processing repository: {repo_name}, saving to {repo_dir}")
    try:
        # Clone or pull the repo
        try:
            repo = git.Repo.clone_from(repo_url, repo_dir)
        except git.exc.GitCommandError:
            # If repo exists, pull latest changes
            repo = git.Repo(repo_dir)
            repo.remotes.origin.pull()

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
        if repo.is_dirty():
            db.add_log(job_id, "github",
                       "Changes detected, committing and pushing")
            repo.git.add(A=True)
            repo.git.commit(m=f"Applied changes via aider: {data['prompt']}")
            repo.git.push()

            # Persist changes to volume
            volumes["github-repos"].commit()
            db.update_job_status(job_id, "completed")
        else:
            db.add_log(job_id, "github", "No changes to commit")
            db.update_job_status(job_id, "completed")

        return f"Successfully ran prompt for repo {repo_name}"
    except Exception as e:
        error_msg = f"Error processing repository: {str(e)}"
        db.add_log(job_id, "backend", error_msg)
        db.update_job_status(job_id, "failed", str(e))
        return error_msg


@app.function(
    volumes=volumes,
    timeout=3600,  # 1 hour
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret")
    ]
)
@modal.web_endpoint(label="create-frame-project", method="POST", docs=True)
def create_frame_project(data: dict) -> dict:
    """Create a new frame project with GitHub repo and Vercel deployment."""
    import os
    from github import Github
    import requests
    from openai import OpenAI
    import uuid
    import base64
    import time

    def validate_input(data: dict) -> None:
        required_fields = ["prompt", "description", "fid"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def verify_github_setup(gh: Github, job_id: str, db: Database) -> None:
        """Verify GitHub token and organization access"""
        required_scopes = ['repo', 'admin:org']

        try:
            # Check authentication
            user = gh.get_user()
            db.add_log(job_id, "github",
                       f"Authenticated as GitHub user: {user.login}")

            # Check organization access
            org = gh.get_organization(GITHUB_ORG_NAME)
            db.add_log(job_id, "github", f"Successfully accessed organization: {
                       GITHUB_ORG_NAME}")

            # Check if user has admin access to org
            try:
                membership = org.get_membership(user.login)
                if membership.role not in ['admin', 'owner']:
                    raise Exception(f"User {user.login} needs admin access to {
                                    GITHUB_ORG_NAME}")
            except Exception as e:
                raise Exception(
                    f"Failed to verify organization membership: {str(e)}")

        except Exception as e:
            raise Exception(f"GitHub setup verification failed: {str(e)}")

    def generate_random_secret() -> str:
        """Generate a random secret for NextAuth"""
        return base64.b64encode(os.urandom(32)).decode('utf-8')

    def sanitize_project_name(name: str) -> str:
        """Sanitize project name for Vercel compatibility"""
        import re
        sanitized = re.sub(r'[^a-z0-9._-]', '-', name.lower())
        sanitized = re.sub(r'-+', '-', sanitized)
        sanitized = sanitized[:100].strip('-')
        return sanitized or 'new-frame-project'

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

    def setup_github_repo(gh: Github, sanitized_name: str, description: str) -> tuple:
        """Create and setup GitHub repository"""
        try:
            # Try to get the organization
            try:
                org = gh.get_organization(GITHUB_ORG_NAME)
                db.add_log(job_id, "github", f"Successfully connected to organization: {
                           GITHUB_ORG_NAME}")
            except Exception as e:
                raise Exception(f"Unable to access organization '{
                                GITHUB_ORG_NAME}'. Error: {str(e)}")

            # Check if repo already exists
            try:
                existing_repo = org.get_repo(sanitized_name)
                if existing_repo:
                    raise Exception(f"Repository '{sanitized_name}' already exists in {
                                    GITHUB_ORG_NAME}")
            except Exception as e:
                if "Not Found" not in str(e):
                    raise

            # Create repo in the organization
            try:
                repo = org.create_repo(
                    name=sanitized_name,
                    description=description,
                    private=False
                )
                db.add_log(job_id, "github",
                           f"Created new repository: {repo.html_url}")
            except Exception as e:
                raise Exception(f"Failed to create repository: {str(e)}")

            # Copy template contents
            try:
                # Access the template from user's repository
                template_repo = gh.get_repo("hellno/farcaster-frames-template")
            except Exception as e:
                raise Exception(f"Failed to access template repository: {str(e)}")

            try:
                contents = template_repo.get_contents("")
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(
                            template_repo.get_contents(file_content.path))
                    else:
                        try:
                            template_content = template_repo.get_contents(
                                file_content.path).decoded_content
                            repo.create_file(
                                file_content.path,
                                f"Copy template file {file_content.path}",
                                template_content
                            )
                        except Exception as e:
                            db.add_log(job_id, "github", f"Warning: Failed to copy {
                                       file_content.path}: {str(e)}")
                            # Continue with other files even if one fails
                            continue

                db.add_log(job_id, "github",
                           "Successfully copied template files")
                return repo

            except Exception as e:
                raise Exception(f"Failed to copy template contents: {str(e)}")

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

        project_data = {
            "name": sanitized_name,
            "framework": "nextjs",
            "gitRepository": {
                "type": "github",
                "repo": repo.full_name
            },
            "environmentVariables": [
                {
                    "key": "NEXTAUTH_SECRET",
                    "value": generate_random_secret(),
                    "target": ["production"],
                    "type": "secret"
                },
                {
                    "key": "KV_REST_API_URL",
                    "value": os.environ["KV_REST_API_URL"],
                    "target": ["production"],
                    "type": "secret"
                },
                {
                    "key": "KV_REST_API_TOKEN",
                    "value": os.environ["KV_REST_API_TOKEN"],
                    "target": ["production"],
                    "type": "secret"
                }
            ]
        }

        vercel_project = requests.post(
            f"https://api.vercel.com/v9/projects?teamId={
                os.environ['VERCEL_TEAM_ID']}",
            headers=vercel_headers,
            json=project_data
        ).json()

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

        return deployment

    # Main execution flow
    db = Database()
    try:
        validate_input(data)

        # Initialize project record
        project_id = db.create_project(
            fid_owner=int(data["fid"]),
            repo_url="",
            frontend_url=""
        )

        # Create job to track progress
        job_id = db.create_job(project_id, job_type="setup_project")
        db.add_log(job_id, "backend",
                   f"Starting project creation with prompt: {data['prompt']}")

        # Initialize and verify GitHub client
        try:
            gh = Github(os.environ["GITHUB_TOKEN"])
            verify_github_setup(gh, job_id, db)
        except Exception as e:
            error_msg = f"GitHub setup failed: {str(e)}"
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", error_msg)
            return {"error": error_msg}, 500

        # Initialize OpenAI client
        deepseek = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )

        # Generate and sanitize project name
        project_name = generate_project_name(data["prompt"], deepseek)
        sanitized_name = sanitize_project_name(project_name)

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

            # Trigger initial code update
            trigger_initial_code_update(
                project_id=project_id,
                repo_path=repo_path,
                prompt=data["prompt"],
                db=db,
                job_id=job_id
            )

            # Setup domain association using the Vercel URL
            domain = deployment['url'].split(
                '://')[1]  # Remove https:// prefix
            setup_domain_association(
                project_id=project_id,
                repo_path=repo_path,
                domain=domain,
                db=db,
                job_id=job_id
            )

            db.add_log(job_id, "backend",
                       "All setup steps completed successfully")

        except Exception as e:
            error_msg = f"Error during post-deployment setup: {str(e)}"
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", str(e))
            return {"error": error_msg}, 500

        db.update_job_status(job_id, "completed")
        return {
            "status": "success",
            "projectId": project_id,
            "repoUrl": repo.html_url,
            "vercelUrl": frontend_url,
            "projectName": sanitized_name
        }

    except Exception as e:
        error_msg = f"Error creating project: {str(e)}"
        if 'job_id' in locals():
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", str(e))
        return {"error": error_msg}, 500


@app.function(secrets=[modal.Secret.from_name("farcaster-secret")])
def trigger_initial_code_update(project_id: str, repo_path: str, prompt: str, db: Database, job_id: str) -> None:
    """Trigger initial code update with user's prompt"""
    db.add_log(job_id, "backend", "Triggering initial code update")

    update_response = update_code.remote({
        "projectId": project_id,
        "repoPath": repo_path,
        "prompt": prompt,
        "job_type": "update_code"
    })

    db.add_log(job_id, "backend",
               f"Initial code update completed: {update_response}")


def setup_domain_association(project_id: str, repo_path: str, domain: str, db: Database, job_id: str) -> None:
    """Generate and insert domain association into the project"""
    db.add_log(job_id, "backend", "Setting up domain association")

    # Generate domain association
    domain_assoc = generate_domain_association.remote(domain)

    # Create prompt to update farcaster.json route
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

    # Trigger code update with domain association
    update_response = update_code.remote({
        "projectId": project_id,
        "repoPath": repo_path,
        "prompt": update_prompt
    })

    db.add_log(job_id, "backend",
               f"Domain association setup completed: {update_response}")


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
