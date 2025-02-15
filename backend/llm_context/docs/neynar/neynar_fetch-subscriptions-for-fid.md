# fetch-subscriptions-for-fid

**Endpoint**: `GET /farcaster/user/subscriptions_created`

## Description
Fetch created subscriptions for a given FID's.

## Parameters
- `fid` (query): No description
- `subscription_provider` (query): No description

## Response
```typescript
{'type': 'object', 'properties': {'subscriptions_created': {'type': 'array', 'items': {'$ref': '#/components/schemas/Subscriptions'}}}}
```
