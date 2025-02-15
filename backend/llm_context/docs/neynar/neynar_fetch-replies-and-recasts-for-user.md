# fetch-replies-and-recasts-for-user

**Endpoint**: `GET /farcaster/feed/user/replies_and_recasts`

## Description
Fetch recent replies and recasts for a given user FID; sorted by most recent first

## Parameters
- `fid` (query): FID of user whose replies and recasts you want to fetch
- `filter` (query): filter to fetch only replies or recasts
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
