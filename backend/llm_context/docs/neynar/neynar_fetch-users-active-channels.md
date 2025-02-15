# fetch-users-active-channels

**Endpoint**: `GET /farcaster/channel/user`

## Description
Fetches all channels that a user has casted in, in reverse chronological order.

## Parameters
- `fid` (query): The user's FID (identifier)
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/Channel'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
