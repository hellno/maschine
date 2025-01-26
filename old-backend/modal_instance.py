import modal
from modal import CloudBucketMount
from backend.config.project_config import ProjectConfig
from backend.services.project_volume import ProjectVolume

# Shared base image definition
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .env(ProjectConfig.CONTAINER_ENV_VARS)
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
app = modal.App(name=ProjectConfig.APP_NAME, image=base_image)


# Configure S3 bucket mount for project storage
# Configure S3 bucket mount with hardcoded name
s3_mount = CloudBucketMount(
    bucket_name=ProjectVolume.BUCKET_NAME,
    secret=modal.Secret.from_name("aws-secret"),
    read_only=False,
    key_prefix="projects/"
)

volumes = {
    ProjectVolume.BASE_MOUNT: s3_mount,
    # Preserve existing volumes if needed
    ProjectConfig.PATHS["GITHUB_REPOS"]: modal.Volume.from_name(
        ProjectConfig.VOLUMES["GITHUB_REPOS"], create_if_missing=True),
    "/shared/node_modules": modal.Volume.from_name(
        ProjectConfig.VOLUMES["SHARED_NODE_MODULES"], create_if_missing=True),
    "/pnpm-store": modal.Volume.from_name(
        ProjectConfig.VOLUMES["PNPM_STORE"], create_if_missing=True)
}
