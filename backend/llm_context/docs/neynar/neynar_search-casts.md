# search-casts

**Endpoint**: `GET /farcaster/cast/search`

## Description
Search for casts based on a query string, with optional AND filters

## Parameters
- `q` (query): Query string to search for casts. Include 'before:YYYY-MM-DD' or 'after:YYYY-MM-DD' to search for casts before or after a specific date.
- `author_fid` (query): Fid of the user whose casts you want to search
- `viewer_fid` (query): Providing this will return search results that respects this user's mutes and blocks and includes `viewer_context`.
- `parent_url` (query): Parent URL of the casts you want to search
- `channel_id` (query): Channel ID of the casts you want to search
- `priority_mode` (query): When true, only returns search results from power badge users and users that the viewer follows (if viewer_fid is provided).
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor

## Response
```typescript
{'type': 'object', 'required': ['result'], 'properties': {'result': {'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}}}
```
