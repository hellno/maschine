import modal
from backend import config

CONTAINER_ENV_VARS = {
    "PATH": "/root/.local/share/pnpm/bin:/root/.local/share/pnpm:/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH",
    "PNPM_STORE_PATH": "/pnpm-store",
    "PNPM_HOME": "/root/.local/share/pnpm",
    "SHELL": "/bin/bash",
}

base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .env(CONTAINER_ENV_VARS)
    .apt_install("git", "curl", "python3-dev", "build-essential")
    .pip_install(
        "fastapi",
        "aider-chat[playwright]",
        "GitPython",
        "PyGithub",
        "openai",
        "supabase",
        "sentry-sdk[fastapi]",
        "redis",
        "tenacity",
        "eth-account",
        "boto3",
    )
    .run_commands(
        "playwright install --with-deps chromium",
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        "curl -fsSL https://get.pnpm.io/install.sh | SHELL=/bin/bash bash -",
        "pnpm add -g node-gyp",
    )
)

# Create main app instance
app = modal.App(name=config.APP_NAME, image=base_image)


# s3_mount = CloudBucketMount(
#     bucket_name=config.BUCKET_NAME,
#     secret=modal.Secret.from_name("aws-secret"),
#     read_only=False,
#     key_prefix="projects/",

# )

volumes = {
    # config.BASE_MOUNT: s3_mount,
    config.PATHS["GITHUB_REPOS"]: modal.Volume.from_name(
        config.VOLUMES["GITHUB_REPOS"], create_if_missing=True
    ),
    config.PATHS["SHARED_NODE_MODULES"]: modal.Volume.from_name(
        config.VOLUMES["SHARED_NODE_MODULES"], create_if_missing=True
    ),
    config.PATHS["PNPM_STORE"]: modal.Volume.from_name(
        config.VOLUMES["PNPM_STORE"], create_if_missing=True
    ),
}

all_secrets = [
    modal.Secret.from_name("github-secret"),
    modal.Secret.from_name("vercel-secret"),
    modal.Secret.from_name("llm-api-keys"),
    modal.Secret.from_name("supabase-secret"),
    modal.Secret.from_name("upstash-secret"),
    modal.Secret.from_name("farcaster-secret"),
    modal.Secret.from_name("neynar-secret"),
    modal.Secret.from_name("redis-secret"),
    modal.Secret.from_name("aws-secret"),
]

db_secrets = [
    modal.Secret.from_name("supabase-secret"),
]
