# fetch-ban-list

**Endpoint**: `GET /farcaster/ban/list`

## Description
Fetches all FIDs that your app has banned.

## Parameters
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['bans', 'next'], 'properties': {'bans': {'type': 'array', 'items': {'$ref': '#/components/schemas/BanRecord'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
