import sys
from pathlib import Path
import os

import modal
from .db import Database
from .db import Database

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


@app.function()
def f(i: int) -> int:
    """Square a number and print a message based on its parity.

    Args:
        i: The input number to process

    Returns:
        The square of the input number
    """
    if i % 2 == 0:
        print("hello", i)
    else:
        print("world", i, file=sys.stderr)

    return i * i


@app.local_entrypoint()
def main(num_iterations: int = 200):
    """Run the function in different modes and aggregate results.

    Args:
        num_iterations: Number of parallel iterations to run (default: 200)
    """
    # run the function locally
    print("Local result:", f.local(1000))

    # run the function remotely on Modal
    print("Remote result:", f.remote(1000))

    # run the function in parallel and remotely on Modal
    total = 0
    for ret in f.map(range(num_iterations)):
        total += ret

    print(f"Total from {num_iterations} parallel executions:", total)


@app.function(volumes=volumes,
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
    job_id = db.create_job(data.get("projectId"))
    db.add_log(job_id, "backend", f"Starting code update for repo: {data.get('repoPath')}")

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
            db.add_log(job_id, "github", "Changes detected, committing and pushing")
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

@app.function(volumes=volumes,
                secrets=[
                    modal.Secret.from_name("github-secret"),
                    modal.Secret.from_name("vercel-secret"),
                    modal.Secret.from_name("llm-api-keys"),
                    modal.Secret.from_name("supabase-secret")
                ])
@modal.web_endpoint(label="create-frame-project", method="POST", docs=True)
def create_frame_project(data: dict) -> dict:
    """Create a new frame project with GitHub repo and Vercel deployment.

    Args:
        data: Dict containing prompt, description and fid
    Returns:
        Dict with project status and details
    """
    import os
    from github import Github
    import requests
    from openai import OpenAI
    import uuid
    import base64
    import time

    db = Database()

    # Validate input
    required_fields = ["prompt", "description", "fid"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400

    prompt = data["prompt"]
    description = data["description"]
    fid = data["fid"]

    # Initialize clients
    gh = Github(os.environ["GITHUB_TOKEN"])
    deepseek = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com/v1"
    )

    def generate_random_secret():
        """Generate a random secret for NextAuth"""
        return base64.b64encode(os.urandom(32)).decode('utf-8')

    def sanitize_project_name(name: str) -> str:
        """Sanitize project name for Vercel compatibility"""
        import re
        # Convert to lowercase and replace invalid chars
        sanitized = re.sub(r'[^a-z0-9._-]', '-', name.lower())
        # Remove multiple hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Trim to 100 chars and remove leading/trailing hyphens
        sanitized = sanitized[:100].strip('-')
        return sanitized or 'new-frame-project'

    try:
        # Create project record first
        project_id = db.create_project(
            fid_owner=int(data["fid"]),
            repo_url="",  # Will update later
            frontend_url=""  # Will update later
        )
        
        # Create job to track progress
        job_id = db.create_job(project_id)
        db.add_log(job_id, "backend", f"Starting project creation with prompt: {data['prompt']}")

        # Generate project name using Deepseek
        name_response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Generate a concise, aspirational project name. Only respond with the name."},
                {"role": "user", "content": f"Generate a short project name based on: {prompt}"}
            ],
            temperature=2,
            max_tokens=25
        )
        project_name = name_response.choices[0].message.content.strip()
        sanitized_name = sanitize_project_name(project_name)
    
        # Create GitHub repository
        db.add_log(job_id, "github", f"Creating GitHub repository: {sanitized_name}")
        org = gh.get_organization("frameception-v2")
        repo = org.create_repo(
            name=sanitized_name,
            description=description,
            private=False
        )
        db.add_log(job_id, "github", f"Created GitHub repo: {repo.html_url}")

        # Copy template repository contents
        db.add_log(job_id, "github", "Copying template repository contents")
        template_org = gh.get_organization("hellno")
        template_repo = template_org.get_repo("farcaster-frames-template")
    
        # Get template contents and create in new repo
        contents = template_repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(template_repo.get_contents(file_content.path))
            else:
                try:
                    template_content = template_repo.get_contents(file_content.path).decoded_content
                    repo.create_file(
                        file_content.path,
                        f"Copy template file {file_content.path}",
                        template_content
                    )
                except Exception as e:
                    print(f"Error copying {file_content.path}: {str(e)}")

        # Create Vercel project
        db.add_log(job_id, "vercel", "Creating Vercel project")
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
            f"https://api.vercel.com/v9/projects?teamId={os.environ['VERCEL_TEAM_ID']}",
            headers=vercel_headers,
            json=project_data
        ).json()

        # Trigger deployment
        deployment = requests.post(
            f"https://api.vercel.com/v13/deployments?teamId={os.environ['VERCEL_TEAM_ID']}",
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

        # Update project with final URLs
        frontend_url = f"https://{deployment['url']}"
        db.client.table('projects').update({
            'repo_url': repo.html_url,
            'frontend_url': frontend_url
        }).eq('id', project_id).execute()
        
        db.add_log(job_id, "vercel", f"Deployment created at: {frontend_url}")
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
def generate_domain_association(domain: str) -> dict:
    """Generate a domain association signature for Farcaster frames.
    
    Args:
        domain: The domain to generate association for
        
    Returns:
        Dict containing compact and JSON formats of the signed domain association
    """
    import os
    from eth_account import Account
    import json
    import base64

    try:
        # Get environment variables
        fid = int(os.environ.get("FID", 0))
        custody_address = os.environ.get("CUSTODY_ADDRESS", "")
        private_key = os.environ.get("PRIVATE_KEY", "")

        # Validate inputs and configuration
        if not domain:
            raise ValueError("Domain is required")

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

        # Sign message using ethereum account
        account = Account.from_key(private_key)
        signature_bytes = Account.sign_message(
            Account,
            message.encode('utf-8'),
            private_key
        ).signature
        encoded_signature = base64.urlsafe_b64encode(signature_bytes).decode('utf-8').rstrip('=')

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
