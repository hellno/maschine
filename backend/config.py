GITHUB = {
    "ORG_NAME": "frameception-v2",
    "TEMPLATE_REPO": "https://github.com/hellno/farcaster-frames-template.git",
    "COMMIT_NAME": "hellno",
    "COMMIT_EMAIL": "686075+hellno@users.noreply.github.com",
    "DEFAULT_DESCRIPTION": "A new Farcaster frameception project",
}

APP_NAME = "frameception"

TIMEOUTS = {
    "CODE_UPDATE": 1200,  # 20 mins
    "PROJECT_SETUP": 3600,  # 1 hour
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

BASE_MOUNT = "/s3-projects"
BUCKET_NAME = "frameception-projects-prod"  # Hardcoded bucket name
