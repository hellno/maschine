# fetch-composer-actions

**Endpoint**: `GET /farcaster/cast/composer_actions/list`

## Description
Fetches all composer actions on Warpcast. You can filter by top or featured.

## Parameters
- `list` (query): Type of list to fetch.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'properties': {'actions': {'type': 'array', 'items': {'type': 'object', 'properties': {'name': {'type': 'string', 'description': 'The name of the action.'}, 'icon': {'type': 'string', 'description': 'The icon representing the action.'}, 'description': {'type': 'string', 'description': 'A brief description of the action.'}, 'about_url': {'type': 'string', 'format': 'uri', 'description': 'URL to learn more about the action.'}, 'image_url': {'type': 'string', 'format': 'uri', 'description': "URL of the action's image."}, 'action_url': {'type': 'string', 'format': 'uri', 'description': 'URL to perform the action.'}, 'action': {'type': 'object', 'properties': {'action_type': {'type': 'string', 'description': 'Type of the action (e.g., post).'}, 'post_url': {'type': 'string', 'format': 'uri', 'description': 'URL to post the action.'}}}, 'octicon': {'type': 'string', 'description': 'Icon name for the action.'}, 'added_count': {'type': 'integer', 'description': 'Number of times the action has been added.'}, 'app_name': {'type': 'string', 'description': 'Name of the application providing the action.'}, 'author_fid': {'type': 'integer', 'description': "Author's Farcaster ID."}, 'category': {'type': 'string', 'description': 'Category of the action.'}, 'object': {'type': 'string', 'description': 'Object type, which is "composer_action".'}}}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
