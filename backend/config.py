GITHUB = {
    "ORG_NAME": "frameception-v2",
    "TEMPLATE_REPO": "https://github.com/hellno/farcaster-frames-template.git",
    "COMMIT_NAME": "hellno",
    "COMMIT_EMAIL": "686075+hellno@users.noreply.github.com",
    "DEFAULT_DESCRIPTION": "A new Farcaster frameception project",
}

APP_NAME = "frameception"
MODAL_UPDATE_CODE_FUNCTION_NAME = "update_code"
MODAL_CREATE_PROJECT_FUNCTION_NAME = "create_project"
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

AIDER_CONFIG = {
    "MODEL": {
        # "model": "sonnet",
        # "model": "r1", # deepseek has API issues right now :(
        "model": "openai/deepseek-ai/DeepSeek-R1",  # together.ai via openrouter in env vars
        "editor_model": "sonnet",
    },
    "CODER": {"verbose": False, "cache_prompts": True},
    "MODEL_SETTINGS": {
        "FILENAME": ".aider.model.settings.yml",
        "CONTENT": """- name: openai/deepseek-r1-llama-70b
  edit_format: diff
  weak_model_name: null
  use_repo_map: true
  send_undo_reply: false
  lazy: false
  reminder: sys
  examples_as_sys_msg: true
  cache_control: false
  caches_by_default: true
  use_system_prompt: true
  use_temperature: true
  streaming: true
  remove_reasoning: think
""",
    },
}

FRONTEND_URL = "https://farcasterframeception.vercel.app"
