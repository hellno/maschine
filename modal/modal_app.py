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
    "GitPython"
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
              secrets=[modal.Secret.from_name("github-secret"),
                       modal.Secret.from_name("llm-api-keys")]
              )
@modal.web_endpoint(method="POST", docs=True)
def update_repo_code(data: dict) -> str:
    import git
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    import os

    if not data.get("repo"):
        return "Please provide a repo name in the request body"

    if not data.get("prompt"):
        return "Please provide a prompt in the request body"

    repo_name = data["repo"]

    repo_url = f"https://{os.environ["GITHUB_TOKEN"]
                          }@github.com/{repo_name}.git"
    repo_dir = f"/github-repos/{repo_name.split('/')[-1]}"

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
