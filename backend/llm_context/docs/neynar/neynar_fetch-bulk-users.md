# fetch-bulk-users

**Endpoint**: `GET /farcaster/user/bulk`

## Description
Fetches information about multiple users based on FIDs

## Parameters
- `fids` (query): Comma separated list of FIDs, up to 100 at a time
- `viewer_fid` (query): No description

## Response
```typescript
{'type': 'object', 'required': ['users'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}}}
```
