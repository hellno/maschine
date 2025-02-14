# frameception

![frameception image](docs/image.png)

## System Architecture Overview

```ascii
┌──────────────────────┐     (HTTP POST)
│  External Services   │
│ (Neynar, User Apps)  │────┐
└──────────────────────┘    │
                            ▼
┌─────────────────────────────────────────────────────┐
│               Modal Webhooks                        │
│ ┌──────────────────────┐ ┌────────────────────────┐ │
│ │create_project_webhook│ │handle_farcaster_webhook│ │
│ └─────────┬────────────┘ └────────┬───────────────┘ │
│           │                       │                 │
│           ▼                       ▼                 │
│ ┌───────────────────┐    ┌───────────────────────┐  │
│ │update_code_webhook│    │deploy_project_webhook │  │
│ └───────┬───────────┘    └───────────┬───────────┘  │
└─────────│────────────────────────────│──────────────┘
          ▼                            ▼
        ┌────────────────────────────────┐
        │       Background Jobs          │
        │     ┌────────────────────────┐ │
        │     │create_project          │ │
        │     │deploy_project          │ │
        │     │update_code             │ │
        │     └──────────┬─────────────┘ │
        └────────────────│───────────────┘
                         ▼
┌───────────────────────────────────────────────────────────┐
│                      Service Classes                      │
│ ┌──────────────────┐   ┌────────────────┐   ┌───────────┐ │
│ │CreateProjectSrvce├──►│ GithubApi      │   │VercelApi  │ │
│ └──────┬───────────┘   └───────┬────────┘   └────┬──────┘ │
│        │                       │                 │        │
│        ▼                       ▼                 ▼        │
│ ┌───────────────┐   ┌──────────────────┐ ┌──────────────┐ │
│ │CodeService    │   │Database          │ │NeynarPost    │ │
│ └──────┬────────┘   └──────────────────┘ └───────┬──────┘ │
│        │                                         │        │
│        ▼                                         ▼        │
│ ┌───────────────┐                          ┌─────────────┐│
│ │Aider Coder    │                          │Farcaster API││
│ └───────────────┘                          └─────────────┘│
└───────────────────────────────────────────────────────────┘
```

### Key Components:

1. **Webhook Handlers** - Entry points for external interactions
2. **Background Jobs** - Long-running Modal functions for async processing
3. **Core Services** - Main business logic containers
4. **External Integrations** - Third-party API connections

### Data Flow:

1. User interactions via Farcaster casts trigger `handle_farcaster_webhook`
2. Webhooks create database records and spawn background jobs
3. `CreateProjectService` coordinates GitHub repo + Vercel setup
4. `CodeService` manages AI-driven code modifications
5. `DeployProjectService` handles final deployment verification
6. `NeynarPost` sends social media responses back to users

# Run frontend

pnpm dev

# Deploy backend

```bash
modal deploy backend/main.py
```
