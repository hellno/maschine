# search-channels

**Endpoint**: `GET /farcaster/channel/search`

## Description
Returns a list of channels based on ID or name

## Parameters
- `q` (query): Channel ID or name for the channel being queried
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['channels', 'next'], 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/Channel'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
