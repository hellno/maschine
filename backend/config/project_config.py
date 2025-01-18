class ProjectConfig:
    """Project configuration constants."""
    APP_NAME = "frameception"
    
    GITHUB = {
        "ORG_NAME": "frameception-v2",
        "TEMPLATE_REPO": "https://github.com/hellno/farcaster-frames-template.git",
        "COMMIT_NAME": "hellno",
        "COMMIT_EMAIL": "686075+hellno@users.noreply.github.com"
    }

    VERCEL = {
        "FRAMEWORK": "nextjs",
        "INSTALL_CMD": "yarn install",
        "BUILD_CMD": "yarn build",
        "OUTPUT_DIR": ".next"
    }

    TIMEOUTS = {
        "CODE_UPDATE": 1200,  # 20 mins
        "PROJECT_SETUP": 3600  # 1 hour
    }

    VOLUMES = {
        "GITHUB_REPOS": "frameception-github-repos",
        "SHARED_NODE_MODULES": "frameception-shared-node-modules",
        "PNPM_STORE": "frameception-pnpm-store"
    }

    PATHS = {
        "GITHUB_REPOS": "/github-repos"
    }

    CONTAINER_ENV_VARS = {
        "PATH": "/root/.local/share/pnpm/bin:/root/.local/share/pnpm:/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH",
        "PNPM_STORE_PATH": "/pnpm-store",
        "PNPM_HOME": "/root/.local/share/pnpm",
        "SHELL": "/bin/bash"
    }
