import sys
from pathlib import Path
import os

import modal

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
        "openai"
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
                  modal.Secret.from_name("llm-api-keys")
              ]
              )
@modal.web_endpoint(label="update-code", method="POST", docs=True)
def update_code(data: dict) -> str:
    import git
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    import os

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
            print(f"Repo is dirty, committing changes")
            repo.git.add(A=True)
            repo.git.commit(m=f"Applied changes via aider: {data['prompt']}")
            repo.git.push()

            # Persist changes to volume
            volumes["github-repos"].commit()
        else:
            print("No changes to commit")
        return f"Successfully ran prompt for repo {repo_name}"
    except Exception as e:
        print(f"Error processing repository: {str(e)}")
        print(f'error: {e}')
        return f"Error processing repository: {str(e)} {e}"

@app.function(volumes=volumes,
                secrets=[
                    modal.Secret.from_name("github-secret"),
                    modal.Secret.from_name("vercel-secret"),
                    modal.Secret.from_name("llm-api-keys")
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
        org = gh.get_organization("frameception-v2")
        repo = org.create_repo(
            name=sanitized_name,
            description=description,
            private=False
        )
        print(f"Created GitHub repo: {repo.html_url}")

        # Copy template repository contents
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

        # Return success response
        return {
            "status": "success",
            "projectId": str(uuid.uuid4()),
            "repoUrl": repo.html_url,
            "vercelUrl": f"https://{deployment['url']}",
            "projectName": sanitized_name
        }

    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return {"error": str(e)}, 500
