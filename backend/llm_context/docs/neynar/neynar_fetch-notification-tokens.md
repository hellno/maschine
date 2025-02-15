# fetch-notification-tokens

**Endpoint**: `GET /farcaster/frame/notification_tokens`

## Description
Returns a list of notifications tokens related for an app


## Parameters
- `limit` (query): Number of results to fetch
- `fids` (query): Comma separated list of FIDs, up to 100 at a time

## Response
```typescript
{'type': 'object', 'required': ['notification_tokens', 'next'], 'properties': {'notification_tokens': {'type': 'array', 'items': {'type': 'object', 'properties': {'object': {'type': 'string', 'enum': ['notification_token']}, 'url': {'type': 'string'}, 'token': {'type': 'string'}, 'status': {'type': 'string', 'enum': ['enabled', 'disabled']}, 'fid': {'$ref': '#/components/schemas/Fid'}, 'created_at': {'type': 'string', 'format': 'date-time'}, 'updated_at': {'type': 'string', 'format': 'date-time'}}}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
