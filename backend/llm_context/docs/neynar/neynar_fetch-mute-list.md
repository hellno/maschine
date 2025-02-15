# fetch-mute-list

**Endpoint**: `GET /farcaster/mute/list`

## Description
Fetches all FIDs that a user has muted.

## Parameters
- `fid` (query): The user's FID (identifier)
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['mutes', 'next'], 'properties': {'mutes': {'type': 'array', 'items': {'$ref': '#/components/schemas/MuteRecord'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
