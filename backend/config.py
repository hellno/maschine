GITHUB = {
    "ORG_NAME": "frameception-v2",
    "TEMPLATE_REPO": "https://github.com/hellno/farcaster-frames-template.git",
    "COMMIT_NAME": "hellno",
    "COMMIT_EMAIL": "686075+hellno@users.noreply.github.com",
    "DEFAULT_DESCRIPTION": "A new Farcaster frameception project",
}

SETUP_COMPLETE_COMMIT_MESSAGE = "Setup complete"


APP_NAME = "frameception"
MODAL_UPDATE_CODE_FUNCTION_NAME = "update_code"
MODAL_SETUP_PROJECT_FUNCTION_NAME = "setup_project"
MODAL_DEPLOY_PROJECT_FUNCTION_NAME = "deploy_project"
MODAL_POLL_BUILD_FUNCTION_NAME = "poll_build_status"

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
    "MIN_RAG_SCORE": 0.49,
}

AIDER_CONFIG = {
    "MODEL": {
        "model": "r1",
        "editor_model": "claude-3-5-sonnet-20241022",
    },
    "CODER": {"verbose": False, "cache_prompts": True},
}

FRONTEND_URL = "https://farcasterframeception.vercel.app"
