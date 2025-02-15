# fetch-block-list

**Endpoint**: `GET /farcaster/block/list`

## Description
Fetches all FIDs that a user has blocked or has been blocked by

## Parameters
- `blocker_fid` (query): Providing this will return the users that this user has blocked
- `blocked_fid` (query): Providing this will return the users that have blocked this user
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['blocks', 'next'], 'properties': {'blocks': {'type': 'array', 'items': {'$ref': '#/components/schemas/BlockRecord'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
