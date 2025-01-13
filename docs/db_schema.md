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
| status      | text                    | Job status (pending/in-progress/completed/failed) |
| error       | text                    | Error message if failed |
| logs        | text[]                  | Array of log messages |

## Logs Table

| Column Name  | Type                    | Description |
|-------------|-------------------------|-------------|
| id          | uuid                    | Primary key |
| created_at  | timestamp with timezone | Creation timestamp |
| job_id      | uuid                    | Reference to jobs.id |
| message     | text                    | Log message content |
| level       | text                    | Log level (info/warn/error) |
