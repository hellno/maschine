# fetch-popular-casts-by-user

**Endpoint**: `GET /farcaster/feed/user/popular`

## Description
Fetch 10 most popular casts for a given user FID; popularity based on replies, likes and recasts; sorted by most popular first

## Parameters
- `fid` (query): FID of user whose feed you want to create
- `viewer_fid` (query): No description

## Response
```typescript
{'type': 'object', 'required': ['casts'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}}}
```
