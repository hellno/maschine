import json
from typing import TypedDict, Optional
import modal
import sys
from pathlib import Path
import os
import requests
import datetime
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
from neynar import get_user_casts, format_cast
import sentry_sdk
from notifications import send_notification
import time

# GitHub Configuration
GITHUB_ORG_NAME = "frameception-v2"
TEMPLATE_REPO_URL = "https://github.com/hellno/farcaster-frames-template.git"
GITHUB_COMMIT_NAME = "hellno"
GITHUB_COMMIT_EMAIL = "686075+hellno@users.noreply.github.com"

# Modal Configuration
MODAL_APP_NAME = "frameception"
UPDATE_SNAPSHOT_INTERVAL_DAYS = 1
CODE_UPDATE_TIMEOUT_SECONDS = 1200  # 20 mins
PROJECT_SETUP_TIMEOUT_SECONDS = 3600  # 1 hour

# Volume Names
GITHUB_REPOS_VOLUME_NAME = "frameception-github-repos"

# File Paths
GITHUB_REPOS_PATH = "/github-repos"

# Default Project Files to Modify
DEFAULT_PROJECT_FILES = [
    "src/components/Frame.tsx",
    "src/lib/constants.ts"
]

# Environment Variables for Container
CONTAINER_ENV_VARS = {
    "PATH": "/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
}

# Default Project Files to Modify
DEFAULT_PROJECT_FILES = [
    "src/components/Frame.tsx",
    "src/lib/constants.ts"
]

# File Paths for Domain Association
DOMAIN_ASSOCIATION_PATH = "src/app/.well-known/farcaster.json/route.ts"

# Vercel Configuration
VERCEL_FRAMEWORK = "nextjs"
VERCEL_INSTALL_COMMAND = "yarn install"
VERCEL_BUILD_COMMAND = "yarn build"
VERCEL_OUTPUT_DIR = ".next"

# Notification Settings
DEFAULT_NOTIFICATION_TITLE = "Your {project_name} frame is building"
DEFAULT_NOTIFICATION_BODY = "Frameception has prepared your frame, it's almost ready! 🚀"


def setup_sentry():
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        traces_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )


GITHUB_ORG_NAME = "frameception-v2"

env_vars = {
    "PATH": "/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
}

github_repos = modal.Volume.from_name(
    GITHUB_REPOS_VOLUME_NAME, create_if_missing=True)

volumes = {
    GITHUB_REPOS_PATH: github_repos
}

image = modal.Image.debian_slim(python_version="3.12") \
    .env(CONTAINER_ENV_VARS) \
    .apt_install("git", "curl") \
    .pip_install(
        "fastapi[standard]",
        "aider-chat[playwright]",
        "aider-install",
        "GitPython",
        "PyGithub",
        "requests",
        "openai",
        "supabase",
        "eth-account",
        "sentry-sdk[fastapi]",
        "redis")\
    .run_commands(
        "playwright install --with-deps chromium",
        # Install Node.js
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        # Install yarn
        "npm install -g yarn",
        # Install aider
        "aider-install"
) \
    .run_function(setup_sentry, secrets=[modal.Secret.from_name("sentry-secret")])
app = modal.App(name=MODAL_APP_NAME, image=image)


@app.function(
    secrets=[
        modal.Secret.from_name("github-secret"),
    ]
)
def create_template_snapshot() -> modal.Image:
    """Create a snapshot of the template repository with node_modules installed"""
    import git
    import tempfile

    # Clone template repository
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = git.Repo.clone_from(TEMPLATE_REPO_URL, temp_dir)

        # Create sandbox with Node.js with proper output streaming and resource limits
        with modal.enable_output():
            print('Creating template snapshot...')
            sandbox = modal.Sandbox.create(
                image=modal.Image.debian_slim()
                .apt_install("nodejs", "npm")
                .run_commands("npm install -g yarn"),
                workdir=temp_dir,
                app=modal.App.lookup(MODAL_APP_NAME, create_if_missing=True),
                cpu=2.0,  # 2 CPU cores for build
                memory=4096,  # 4GB RAM
                timeout=1800,  # 30 minutes timeout
            )
            print('sandbox:', sandbox)

            # Tag sandbox for tracking
            sandbox.set_tags({
                "purpose": "template_snapshot",
                "template_version": repo.head.commit.hexsha[:8],
                "created_at": datetime.datetime.now(datetime.UTC).isoformat()
            })
            print('set some tags and run yarn install')

            # Install dependencies
            process = sandbox.exec("yarn", "install")
            print('start yarn install')
            for line in process.stdout:
                print(line.strip())
            process.wait()
            print('yarn install done', process)
            if process.returncode != 0:
                print('Failed to install dependencies')
                raise Exception("Failed to install dependencies")

            # Create snapshot
            print('create snapshot')
            image = sandbox.snapshot_filesystem()

            # No need to call terminate() - Modal will handle cleanup
            return image


@app.function(
    secrets=[modal.Secret.from_name("supabase-secret")]
)
def list_active_sandboxes() -> dict:
    """List all active sandboxes and their status"""
    try:
        sandboxes = []
        app = modal.App.lookup(MODAL_APP_NAME)

        for sandbox in modal.Sandbox.list(app_id=app.app_id):
            tags = sandbox.get_tags()
            sandboxes.append({
                "id": sandbox.object_id,
                "purpose": tags.get("purpose"),
                "project_id": tags.get("project_id"),
                "job_id": tags.get("job_id"),
                "created_at": tags.get("created_at")
            })

        return {
            "status": "success",
            "sandboxes": sandboxes
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.function(
    secrets=[modal.Secret.from_name("supabase-secret")]
)
@modal.web_endpoint(label="list-sandboxes", method="GET")
def list_sandboxes_webhook() -> dict:
    """Webhook to list all active sandboxes
    """
    return list_active_sandboxes.remote()


def sanitize_project_name(name: str) -> str:
    """Sanitize project name for Vercel compatibility"""
    import re
    sanitized = re.sub(r'[^a-z0-9._-]', '-', name.lower())
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized[:100].strip('-')
    return sanitized or 'new-frame-project'


def get_unique_repo_name(gh: Github, base_name: str) -> str:
    """Get a unique repository name by adding/incrementing a number suffix if needed

    Args:
        gh: GitHub client instance
        base_name: Base repository name to check

    Returns:
        str: Unique repository name
    """
    org = gh.get_organization(GITHUB_ORG_NAME)

    # Check if base name exists
    try:
        org.get_repo(base_name)
        # Repo exists, need to modify name
    except:
        # Repo doesn't exist, can use base name
        return base_name

    # Check if name already ends with -number
    number_match = re.match(r'(.+)-(\d+)$', base_name)

    if number_match:
        # Name ends with number, increment it
        name_base = number_match.group(1)
        number = int(number_match.group(2))
        current_try = number + 1
    else:
        # Add -1 to the name
        name_base = base_name
        current_try = 1

    # Keep incrementing until we find an available name
    while True:
        new_name = f"{name_base}-{current_try}"
        try:
            org.get_repo(new_name)
            current_try += 1
            time.sleep(1)
        except:
            return new_name


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


class UserContext(TypedDict):
    fid: int
    username: Optional[str]
    displayName: Optional[str]
    pfpUrl: Optional[str]  # Profile image URL
    location: Optional[dict]  # AccountLocation type


def expand_user_prompt_with_farcaster_context(prompt: str, user_context: UserContext):
    try:
        print(f"Expanding user prompt with Farcaster context: {
              prompt} {user_context}")
        last_ten_casts = get_user_casts(user_context['fid'], 10)
        print('lenght of last ten casts:', len(last_ten_casts))
        formatted_casts = [format_cast(c) for c in last_ten_casts]
        cast_context = '\n'.join([c for c in formatted_casts if c])
        print(f"Cast context: {cast_context}")
        farcaster_context_prompt = f"""Below are the recent Farcaster social media posts from {
            user_context.get("username", "")} {user_context.get("displayName", "")}.
            Take this only as additional context for the core prompt from the user, which is the primary focus and most important thing.
            {cast_context}"""
        return f'{prompt} \n {farcaster_context_prompt}'
    except Exception as e:
        print(f"Error expanding user prompt with Farcaster context: {str(e)}")
        return prompt


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
            {"role": "system", "content": "Generate a concise, aspirational project name. Only respond with the name. No quotation marks, punctuation or quotes."},
            {"role": "user", "content": f"Generate a short project name based on: {prompt}"}
        ],
        temperature=2,
        max_tokens=25
    )
    return name_response.choices[0].message.content.strip()


def get_project_setup_prompt(project_name: str, prompt: str, user_context: UserContext) -> str:
    """Generate a prompt for setting up a new project"""
    return f"""
    Project name: "{project_name}"
    Owner: {user_context.get("username", "")} {user_context.get("displayName", "")}
    User prompt: {prompt}
    """


def improve_user_instructions(prompt: str, deepseek: OpenAI) -> str:
    """Improve user instructions using Deepseek AI"""
    improve_user_instructions_prompt = f"""Take the user’s prompt about a Farcaster frame miniapp and rewrite it as a clear, structured starter prompt for a coding LLM.
    Emphasize a single-page React+TypeScript app using Shadcn UI, Tailwind, wagmi, viem, and minimal Farcaster interactions.
    Keep the output concise, static or minimally dynamic, and aligned with best practices.
    Make sure to update template files and constants as needed to customize the app with title, description and functionality.
    Include:
        1.	A short restatement of the user request with any clarifications (UI, UX, integrations).
        2.	A concise coding plan referencing key components, blockchain hooks, design guidelines, and ensuring a simple one-page layout.
    Your final response: the improved starter prompt, ready for the coding LLM.
    """
    print(f"Improving user instructions: {prompt}")
    try:
        instructions_response = deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": improve_user_instructions_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        print(f"Improved user instructions: {
              json.dumps(instructions_response)}")
        return instructions_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error improving user instructions: {str(e)}")
        return prompt


@app.function()
@modal.web_endpoint(label="update-code", method="POST", docs=True)
def update_code_webhook(data: dict) -> str:
    """Webhook endpoint to trigger code update for a repository"""
    if not data.get("project_id") or not data.get("prompt"):
        return "Please provide project_id and prompt in the request body", 400

    print(f"Received updated code webhook request {data}")
    update_code.remote(data)
    return "Code update initiated"


@app.function(
    retries=1,
    volumes=volumes,
    timeout=CODE_UPDATE_TIMEOUT_SECONDS,
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("neynar-secret"),
        modal.Secret.from_dict({"MODAL_LOGLEVEL": "DEBUG"}),
    ]
)
def update_code(data: dict) -> str:
    import git
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    import os

    print('Received updated code request:', data)
    prompt = data.get("prompt")
    if not prompt:
        return "Please provide a prompt in the request body", 400

    user_context = data.get("user_context")
    project_id = data.get("project_id")
    job_type = data.get("job_type", "update_code")

    db = Database()
    project = db.get_project(project_id)
    if not project:
        return "Project not found", 404
    job_id = db.create_job(project_id,
                           job_type=job_type,
                           data=data)

    repo_path = project.get("repo_url").replace("https://github.com/", "")
    db.add_log(job_id, "backend",
               f"Start code update for repo: {repo_path}")

    repo_url = f"https://{os.environ["GITHUB_TOKEN"]
                          }@github.com/{repo_path}.git"
    repo_dir = f"/github-repos/{repo_path}"

    print(f"Processing repository: {repo_path}, saving to {repo_dir}")
    try:
        # Get template snapshot when needed
        template_snapshot = create_template_snapshot.remote()

        is_repo_stored_locally = os.path.exists(repo_dir)
        repo = None
        if not is_repo_stored_locally:
            repo = git.Repo.clone_from(
                repo_url, repo_dir, depth=1, single_branch=True, branch="main")
            repo.config_writer().set_value("user", "name", GITHUB_COMMIT_NAME).release()
            repo.config_writer().set_value(
                "user", "email", GITHUB_COMMIT_EMAIL).release()

        else:
            repo = git.Repo(repo_dir)
            # Configure git before operations
            repo.config_writer().set_value("user", "name", "hellno").release()
            repo.config_writer().set_value(
                "user", "email", "686075+hellno@users.noreply.github.com").release()

            try:
                # Fetch latest changes
                db.add_log(job_id, "backend",
                           "Fetching latest changes from remote")
                repo.remotes.origin.fetch()

                # Try to pull, handling potential conflicts
                try:
                    repo.git.pull('origin', 'main')
                except git.GitCommandError as pull_error:
                    # If there are conflicts, reset to remote state
                    db.add_log(job_id, "backend",
                               "Conflicts detected, resetting to remote state")
                    repo.git.reset('--hard', 'origin/main')
                    repo.git.clean('-fd')

            except Exception as e:
                db.add_log(job_id, "backend",
                           f"Warning: Error syncing with remote: {str(e)}")
                # If all sync attempts fail, reset the repository
                db.add_log(job_id, "backend",
                           "Performing full repository reset")
                repo.git.reset('--hard')
                repo.git.clean('-fd')
                repo.remotes.origin.pull('main', force=True)

        # Create sandbox with proper resource limits and output streaming
        with modal.enable_output():
            sandbox = modal.Sandbox.create(
                image=template_snapshot,
                workdir=repo_dir,
                app=modal.App.lookup(MODAL_APP_NAME, create_if_missing=True),
                cpu=2.0,
                memory=4096,
                timeout=CODE_UPDATE_TIMEOUT_SECONDS,
                secrets=[
                    modal.Secret.from_name("github-secret"),
                    modal.Secret.from_name("vercel-secret")
                ]
            )

            # Tag sandbox for tracking
            sandbox.set_tags({
                "purpose": "code_update",
                "project_id": project_id,
                "job_id": job_id,
                "repo_path": repo_path,
                "created_at": datetime.datetime.now(datetime.UTC).isoformat()
            })

        # Verify dependencies
        db.add_log(job_id, "backend", "Verifying dependencies")
        process = sandbox.exec("yarn", "install", "--check-files")
        for line in process.stdout:
            db.add_log(job_id, "backend", line.strip())

        def sandbox_test_cmd(cmd: str) -> Optional[str]:
            """Run a command in the sandbox and return error output if it fails, None if successful"""
            try:
                cmd_parts = cmd.split()
                db.add_log(job_id, "backend",
                           f"Running command in sandbox: {cmd}")
                process = sandbox.exec(*cmd_parts)

                # Collect all output
                output = []
                for line in process.stdout:
                    line_str = line.strip()
                    output.append(line_str)
                    db.add_log(job_id, "backend", line_str)

                process.wait()

                # If command failed, return the output as error message
                if process.returncode != 0:
                    error_msg = "\n".join(output)
                    db.add_log(job_id, "backend",
                               f"Command failed with output: {error_msg}")
                    return error_msg

                # Command succeeded
                db.add_log(job_id, "backend", "Command completed successfully")
                return None

            except Exception as e:
                error_msg = f"Error running command in sandbox: {str(e)}"
                db.add_log(job_id, "backend", error_msg)
                return error_msg

        # Test the sandbox_test_cmd with various scenarios
        test_commands = [
            "yarn --version",  # Should succeed
            "yarn lint",       # Should succeed if code is valid
            "yarn invalid",    # Should fail and return error message
            "echo 'test'"      # Should succeed
        ]

        db.add_log(job_id, "backend", "Testing sandbox command execution...")
        for test_cmd in test_commands:
            db.add_log(job_id, "backend", f"\nTesting command: {test_cmd}")
            result = sandbox_test_cmd(test_cmd)
            if result is None:
                db.add_log(job_id, "backend",
                           f"✅ Command succeeded: {test_cmd}")
            else:
                db.add_log(job_id, "backend", f"❌ Command failed: {
                           test_cmd}\nError: {result}")

        os.chdir(repo_dir)  # Change to repo directory
        fnames = [
            f"{repo.working_tree_dir}/{fname}"
            for fname in DEFAULT_PROJECT_FILES
        ]

        # Get all files from llm_docs directory
        llm_docs_dir = f"{repo.working_tree_dir}/llm_docs"
        read_only_fnames = []
        if os.path.exists(llm_docs_dir):
            read_only_fnames = [
                os.path.join(llm_docs_dir, f)
                for f in os.listdir(llm_docs_dir)
                if os.path.isfile(os.path.join(llm_docs_dir, f))
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
            io=io,
            auto_test=True,
            test_cmd=sandbox_test_cmd,  # Use our sandbox test command
            read_only_fnames=read_only_fnames
            # if we want to use yarn build, separate into beefier cpu/memory function
            # like they do on vercel: https://vercel.com/docs/limits/overview#build-container-resources
        )
        print(f'coder: {coder}')
        should_expand_prompt = any(word in prompt.lower() for word in [
            'farcaster',
            ' me ',
            ' my ',
            ' mine ',
            ' myself ',
            ' i ',
            ' we ',
            ' our ',
            '@',  # Catch mentions
            'cast',  # Catch references to Farcaster casts
            'profile'  # Catch references to user profiles
        ])

        if should_expand_prompt and user_context:
            prompt = expand_user_prompt_with_farcaster_context(
                prompt, user_context)
        print(f'Prompt for aider: {prompt}\nmodel: {model}\nfnames: {
              fnames}\ncwd: {repo.working_tree_dir}\ncoder: {coder}')

        res = coder.run(prompt)
        print(f"Result from aider (first 250 chars): {res[:250]}")
        try:
            print(f"Last 5 lines from aider output: {res.splitlines()[-5:]}")
        except Exception as e:
            print(f"Error getting last line of output: {e}")
        db.add_log(job_id, "backend", f"Finished code update")
        db.update_job_status(job_id, "completed")

        try:
            repo.git.push()
        except git.GitCommandError as push_error:
            if "fetch first" in str(push_error):
                db.add_log(job_id, "backend",
                           "Push rejected, trying to sync and retry")
                # Pull latest changes
                repo.remotes.origin.pull('main')
                # Try push again
                repo.git.push()
            else:
                raise
        # No need for explicit termination
        volumes["/github-repos"].commit()
        return f"Successfully ran prompt for repo {repo_path} in project {project_id}"
    except Exception as e:
        if 'repo' in locals() and repo:
            try:
                repo.git.push()
            except:
                pass
        if 'sandbox' in locals() and sandbox:
            try:
                sandbox.terminate()
            except:
                pass

        volumes["/github-repos"].commit()
        print(f"Error updating code: {e}")
        error_msg = f"Error updating code: {str(e)}"
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

    db = Database()

    try:
        required_fields = ["prompt", "description", "userContext"]
        for field in required_fields:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, 400

        fid = int(data["userContext"]["fid"])
        project_id = db.create_project(
            fid_owner=fid,
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


def get_shortest_vercel_domain(project_name: str) -> str:
    """Get the shortest production domain for a Vercel project"""
    vercel_headers = {
        "Authorization": f"Bearer {os.environ['VERCEL_TOKEN']}",
        "Content-Type": "application/json"
    }

    url = f"https://api.vercel.com/v10/projects/{
        project_name}/domains?teamId={os.environ['VERCEL_TEAM_ID']}"
    response = requests.get(url, headers=vercel_headers)
    response.raise_for_status()

    domains = response.json().get("domains", [])
    print(f"Domains for project {project_name}: {domains}")
    if not domains or len(domains) == 0:
        raise ValueError("No domains found for project")

    # Find the shortest valid production domain
    production_domains = [d["name"]
                          for d in domains if d.get("verified", False)]
    if production_domains:
        return min(production_domains, key=len)

    print(f"No verified production domains found for project {project_name}")
    return domains[0]["name"].replace('.', '').replace('*', '')


def cleanup_project_repo(repo_path: str) -> None:
    """Clean up project repository from local storage

    Args:
        repo_path: Path to the repository in the volume
    """
    import shutil

    try:
        full_path = f"/github-repos/{repo_path}"
        if os.path.exists(full_path):
            print(f"Cleaning up repository at {full_path}")
            shutil.rmtree(full_path)
            print(f"Successfully removed repository directory")
        else:
            print(f"No repository found at {full_path} to clean up")
    except Exception as e:
        print(f"Error cleaning up repository {repo_path}: {str(e)}")
        # Don't raise the exception - cleanup failure shouldn't fail the whole process


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

        # Convert signature to hex string prefixed with 0x, then base64url encode
        signature_hex = "0x" + signed_message.signature.hex()
        encoded_signature = base64.urlsafe_b64encode(
            signature_hex.encode("utf-8")
        ).decode("utf-8").rstrip("=")

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
    retries=1,
    volumes=volumes,
    timeout=PROJECT_SETUP_TIMEOUT_SECONDS,
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("vercel-secret"),
        modal.Secret.from_name("llm-api-keys"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("upstash-secret"),
        modal.Secret.from_name("farcaster-secret"),
        modal.Secret.from_name("redis-secret"),
        modal.Secret.from_dict({"MODAL_LOGLEVEL": "DEBUG"})
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

    def setup_github_repo(gh: Github, repo_name: str, description: str) -> object:
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
                existing_repo = org.get_repo(repo_name)
                if existing_repo:
                    raise Exception(
                        f"Repository '{repo_name}' already exists")
            except Exception as e:
                if "Not Found" not in str(e):
                    raise

            # Create new repo
            repo = org.create_repo(
                name=repo_name,
                description=description,
                private=False
            )
            db.add_log(job_id, "github",
                       f"Created repository: {repo.html_url}")

            # Create temporary directory for local operations
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Clone template repository
                    template_path = os.path.join(temp_dir, "template")
                    git.Repo.clone_from(TEMPLATE_REPO_URL, template_path)
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

    def create_vercel_deployment(repo_name: str, repo: object) -> tuple:
        """Create Vercel project and trigger deployment"""
        vercel_headers = {
            "Authorization": f"Bearer {os.environ['VERCEL_TOKEN']}",
            "Content-Type": "application/json"
        }

        # First create the project
        project_data = {
            "name": repo_name,
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
                    repo_name}/env?teamId={os.environ['VERCEL_TEAM_ID']}",
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
                "name": repo_name,
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

        return vercel_project, deployment

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

        user_context = data.get("userContext")
        project_name = generate_project_name(data["prompt"], deepseek)
        username = user_context["username"]
        base_repo_name = f'{username}-{sanitize_project_name(project_name)}'
        repo_name = get_unique_repo_name(gh, base_repo_name)

        # Setup GitHub repository
        db.add_log(job_id, "github",
                   f"Creating GitHub repository: {repo_name}")
        repo = setup_github_repo(gh, repo_name, data["description"])
        db.add_log(job_id, "github", f"Created GitHub repo: {repo.html_url}")

        # Create Vercel deployment
        db.add_log(job_id, "vercel", "Creating Vercel project")
        vercel_project, deployment = create_vercel_deployment(
            repo_name, repo)

        # Store only Vercel project info
        db.update_project_vercel_info(project_id, vercel_project)

        # Get shortest production URL
        frontend_url = f"https://{get_shortest_vercel_domain(repo_name)}"
        if not frontend_url:
            raise Exception("Failed to get valid deployment URL")

        db.client.table('projects').update({
            'name': project_name,
            'repo_url': repo.html_url,
            'frontend_url': frontend_url
        }).eq('id', project_id).execute()

        db.add_log(job_id, "vercel", f"Deployment created at: {frontend_url}")

        try:
            repo_path = repo.full_name
            prompt = get_project_setup_prompt(
                project_name, data["prompt"], user_context)
            prompt = improve_user_instructions(prompt, deepseek)
            code_update_response = update_code.remote({
                "project_id": project_id,
                "repo_path": repo_path,
                "prompt": prompt,
                "user_context": user_context,
                "job_type": "update_code_for_setup"
            })
            db.add_log(job_id, "backend", f"Initial code update completed: {
                       code_update_response}")

            # Add metadata update after initial code update
            metadata_update_prompt = f"""
            Update the following files to customize the project metadata:

            1. In src/lib/constants.ts:
            set PROJECT_ID to "{project_name}"
            set PROJECT_TITLE to "{project_name}"
            set PROJECT_DESCRIPTION to a brief description of the project

            2. In src/app/opengraph-image.tsx:
            - Update the OpenGraph image to reflect the project "{project_name}"
            - Use a relevant background color and layout that matches the project theme
            - Include the project name prominently
            - Add a brief description if space allows
            - Keep the Farcaster Frame branding but make it specific to this project

            Make sure the changes maintain type safety and follow the existing code structure.
            """

            try:
                metadata_update_response = update_code.remote({
                    "project_id": project_id,
                    "repo_path": repo_path,
                    "prompt": metadata_update_prompt,
                    "job_type": "update_code_for_metadata"
                })
                db.add_log(job_id, "backend", f"Metadata update completed: {
                           metadata_update_response}")
            except Exception as e:
                error_msg = f"Error updating project metadata: {str(e)}"
                db.add_log(job_id, "backend", error_msg)
                # Continue with setup even if metadata update fails
                print(f"Warning: {error_msg}")

            print("Starting post-deployment setup with deployment data", deployment)
            # Extract and validate domain
            try:
                print("\n--- Domain Extraction ---")
                print("Raw deployment URL:", frontend_url)
                print("Initial domain value:", frontend_url)
                domain = frontend_url
                if not domain:
                    raise ValueError("Deployment URL is empty")

                if domain.startswith('https://'):
                    print("Removing https:// prefix")
                    domain = domain[8:]

                print("Final processed domain:", domain)
                db.add_log(job_id, "backend", f"Extracted domain: {domain}")
            except Exception as e:
                print("❌ Domain extraction failed:", str(e))
                raise Exception(
                    f"Failed to extract domain from deployment: {str(e)}")

            try:
                print("Calling generate_domain_association with domain:", domain)
                domain_assoc = generate_domain_association(domain)
                print("\nDomain Association Response:", domain_assoc)

                if not isinstance(domain_assoc, dict):
                    raise ValueError(f"Invalid domain association type: {
                                     type(domain_assoc)}")

                required_keys = ['header', 'payload', 'signature']
                print("\nChecking required keys in domain_assoc['json']:")
                if 'json' in domain_assoc:
                    for key in required_keys:
                        present = key in domain_assoc['json']
                        if not present:
                            raise ValueError(
                                f"Missing '{key}' in domain association json")

                print("\n✅ Domain association validation successful")
                print("Final domain_assoc structure:",
                      json.dumps(domain_assoc, indent=2))
                db.add_log(job_id, "backend",
                           "Generated valid domain association")

            except Exception as e:
                print("❌ Domain association generation failed:", str(e))
                print("Full error:", e)
                raise Exception(
                    f"Failed to generate domain association: {str(e)}")

            # Create prompt for domain association update
            update_prompt = f"""
            Update the file src/app/.well-known/farcaster.json/route.ts
            It should return the following domain association in the field accountAssociation:
            {json.dumps(domain_assoc['json'], indent=2)}

            Keep the rest of the config, only update the accountAssociation field.
            """

            # Update domain association
            domain_update_response = update_code.remote({
                "project_id": project_id,
                "repo_path": repo_path,
                "prompt": update_prompt,
                "job_type": "update_code_for_domain_association"
            })
            db.add_log(job_id, "backend", f"Domain association update completed: {
                       domain_update_response}")

            db.add_log(job_id, "backend",
                       "All setup steps completed successfully")
            db.update_job_status(job_id, "completed")

            # Send notification to user
            if user_context and "fid" in user_context:
                try:
                    notification_result = send_notification(
                        fid=user_context["fid"],
                        title=f"Your {project_name} frame is building",
                        body=f"Frameception has prepared your frame, it's almost ready! 🚀",
                    )
                    print(f'sending notification result: {
                          notification_result}')
                    if notification_result["state"] == "success":
                        db.add_log(job_id, "backend", f"Successfully sent completion notification to FID {
                            user_context['fid']}")
                except Exception as e:
                    print(f'Error when sending notifications: {e}')

            # Clean up repository files
            try:
                cleanup_project_repo(repo.full_name)
                print(f"Cleaned up repository files for {repo.full_name}")
            except Exception as e:
                print(
                    f"Warning: Failed to clean up repository files: {str(e)}")

        except Exception as e:
            error_msg = f"Error during post-deployment setup: {str(e)}"
            db.add_log(job_id, "backend", error_msg)
            db.update_job_status(job_id, "failed", str(e))

            # Attempt cleanup even on failure
            if 'repo' in locals() and repo:
                try:
                    cleanup_project_repo(repo.full_name)
                    print(f"Cleaned up repository files after error")
                except Exception as cleanup_error:
                    print(f"Warning: Failed to clean up repository files after error: {
                          str(cleanup_error)}")

    except Exception as e:
        error_msg = f"Error creating project: {str(e)}"
        print('Error setup_frame_project:', error_msg)
        db.update_job_status(job_id, "failed", str(e))


@app.function(
    secrets=[
        modal.Secret.from_name("github-secret"),
    ]
)
@modal.web_endpoint(label="update-template-snapshot-webhook", method="POST")
def update_template_snapshot_webhook() -> dict:
    """Webhook to manually trigger a template snapshot update.

    Usage:
        curl -X POST <endpoint>
    """
    try:
        new_snapshot = create_template_snapshot.remote()

        return {
            "status": "success",
            "message": "Template snapshot updated successfully",
            "timestamp": str(datetime.datetime.now(datetime.UTC))
        }

    except Exception as e:
        error_msg = f"Failed to update template snapshot: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": str(datetime.datetime.now(datetime.UTC))
        }, 500


@app.function(
    secrets=[
        modal.Secret.from_name("redis-secret")
    ]
)
@modal.web_endpoint(label="send-test-notification", method="POST", docs=True)
def send_test_notification(data: dict) -> dict:
    """Temporary webhook endpoint to test sending notifications to a user's FID"""
    try:
        # Validate input
        if 'fid' not in data:
            return {"error": "Missing required field: fid"}, 400

        fid = int(data['fid'])
        title = data.get('title', 'Test Notification')
        body = data.get(
            'body', 'This is a test notification from Frameception')

        # Send notification
        notification_result = send_notification(
            fid=fid,
            title=title,
            body=body
        )

        print(f"Notification result: {notification_result}")
        return {
            "status": "success",
            "result": notification_result
        }

    except Exception as e:
        error_msg = f"Error sending test notification: {str(e)}"
        print(error_msg)
        return {"error": error_msg}, 500
