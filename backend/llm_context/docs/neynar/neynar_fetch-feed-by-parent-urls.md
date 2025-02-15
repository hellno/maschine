# fetch-feed-by-parent-urls

**Endpoint**: `GET /farcaster/feed/parent_urls`

## Description
Fetch feed based on parent URLs

## Parameters
- `parent_urls` (query): Comma separated list of parent_urls
- `with_recasts` (query): Include recasts in the response, true by default
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `with_replies` (query): Include replies in the response, false by default
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
