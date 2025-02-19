GITHUB = {
    "ORG_NAME": "frameception-v2",
    "TEMPLATE_REPO": "https://github.com/hellno/farcaster-frames-template.git",
    "COMMIT_NAME": "hellno",
    "COMMIT_EMAIL": "686075+hellno@users.noreply.github.com",
    "DEFAULT_DESCRIPTION": "A new Farcaster frameception project",
}

APP_NAME = "frameception"
MODAL_UPDATE_CODE_FUNCTION_NAME = "update_code"
MODAL_SETUP_PROJECT_FUNCTION_NAME = "setup_project"
MODAL_DEPLOY_PROJECT_FUNCTION_NAME = "deploy_project"

TIMEOUTS = {
    "CODE_UPDATE": 1200,  # 20 mins
    "PROJECT_SETUP": 3600,  # 1 hour
    "BUILD": 600,  # 10 mins
}

VOLUMES = {
    "GITHUB_REPOS": "frameception-github-repos",
    "SHARED_NODE_MODULES": "frameception-shared-node-modules",
    "PNPM_STORE": "frameception-pnpm-store",
}

PATHS = {
    "GITHUB_REPOS": "/github-repos",
    "SHARED_NODE_MODULES": "/shared/node_modules",
    "PNPM_STORE": "/pnpm-store",
}

CODE_CONTEXT = {
    "ENABLED": True,
}

AIDER_CONFIG = {
    "MODEL": {
        "model": "openai/deepseek-r1-671b",  # venice.ai
        "editor_model": "sonnet",
        # "model": "r1", # official deepseek
        # "model": "sonnet",
        # "model": "openai/deepseek-ai/DeepSeek-R1",  # together.ai via openrouter in env vars
    },
    "CODER": {"verbose": False, "cache_prompts": True},
}

FRONTEND_URL = "https://farcasterframeception.vercel.app"
