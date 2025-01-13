# Database Schema
## Projects Table

| Column Name   | Type                    | Description |
|--------------|-------------------------|-------------|
| id           | uuid                    | Primary key |
| created_at   | timestamp with timezone | Creation timestamp |
| fid_owner    | bigint                 | Farcaster ID of owner |
| repo_url     | text                   | GitHub repository URL |
| frontend_url | text                   | Deployed frontend URL |

## Jobs Table

| Column Name  | Type                    | Description |
|-------------|-------------------------|-------------|
| id          | uuid                    | Primary key |
| created_at  | timestamp with timezone | Creation timestamp |
| project_id  | uuid                    | Reference to projects.id |
| status      | text                    | Job status  |
| data        | jsonb                   | data |

## Logs Table

| Column Name  | Type                    | Description |
|-------------|-------------------------|-------------|
| id          | uuid                    | Primary key |
| created_at  | timestamp with timezone | Creation timestamp |
| job_id      | uuid                    | Reference to jobs.id |
| source      | text                    | Log origin |
| text        | text                    | Log text |

## Enums

source: ['frontend', 'backend', 'vercel', 'github', 'farcaster', 'unknown']
status: ['pending', 'completed', 'failed']
job type: ['setup_project', 'update_code', ]

## Indexes
pkey on each table