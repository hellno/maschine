# fetch-subscribers-for-fid

**Endpoint**: `GET /farcaster/user/subscribers`

## Description
Fetch subscribers for a given FID's contracts. Doesn't return addresses that don't have an FID.

## Parameters
- `fid` (query): No description
- `viewer_fid` (query): No description
- `subscription_provider` (query): No description

## Response
```typescript
{'type': 'object', 'properties': {'subscribers': {'type': 'array', 'items': {'$ref': '#/components/schemas/Subscriber'}}}}
```
