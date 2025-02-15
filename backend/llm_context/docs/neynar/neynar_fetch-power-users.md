# fetch-power-users

**Endpoint**: `GET /farcaster/user/power`

## Description
Fetches power users based on Warpcast power badges. Information is updated once a day.

## Parameters
- `viewer_fid` (query): No description
- `limit` (query): Number of power users to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
