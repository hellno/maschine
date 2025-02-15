# fetch-casts-for-user

**Endpoint**: `GET /farcaster/feed/user/casts`

## Description
Fetch casts for a given user FID in reverse chronological order. Also allows filtering by parent_url and channel

## Parameters
- `fid` (query): FID of user whose recent casts you want to fetch
- `viewer_fid` (query): FID of the user viewing the feed
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor
- `include_replies` (query): Include reply casts by the author in the response, true by default
- `parent_url` (query): Parent URL to filter the feed; mutually exclusive with channel_id
- `channel_id` (query): Channel ID to filter the feed; mutually exclusive with parent_url

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
