# fetch-all-channels

**Endpoint**: `GET /farcaster/channel/list`

## Description
Returns a list of all channels with their details

## Parameters
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['channels'], 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/Channel'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
