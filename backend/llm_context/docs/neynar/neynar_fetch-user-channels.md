# fetch-user-channels

**Endpoint**: `GET /farcaster/user/channels`

## Description
Returns a list of all channels with their details that a FID follows.

## Parameters
- `fid` (query): The FID of the user.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['channels'], 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/Channel'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
