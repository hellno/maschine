# fetch-trending-channels

**Endpoint**: `GET /farcaster/channel/trending`

## Description
Returns a list of trending channels based on activity

## Parameters
- `time_window` (query): No description
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['channels', 'next'], 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/ChannelActivity'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
