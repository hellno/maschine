# fetch-user-following-feed

**Endpoint**: `GET /farcaster/feed/following`

## Description
Fetch feed based on who a user is following

## Parameters
- `fid` (query): FID of user whose feed you want to create
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `with_recasts` (query): Include recasts in the response, true by default
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
