# fetch-frames-only-feed

**Endpoint**: `GET /farcaster/feed/frames`

## Description
Fetch feed of casts with Frames, reverse chronological order

## Parameters
- `limit` (query): Number of results to fetch
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
