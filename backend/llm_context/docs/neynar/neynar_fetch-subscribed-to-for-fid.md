# fetch-subscribed-to-for-fid

**Endpoint**: `GET /farcaster/user/subscribed_to`

## Description
Fetch what FIDs and contracts a FID is subscribed to.

## Parameters
- `fid` (query): No description
- `viewer_fid` (query): No description
- `subscription_provider` (query): No description

## Response
```typescript
{'type': 'object', 'properties': {'subscribed_to': {'type': 'array', 'items': {'$ref': '#/components/schemas/SubscribedTo'}}}}
```
