# fetch-feed-by-channel-ids

**Endpoint**: `GET /farcaster/feed/channels`

## Description
Fetch feed based on channel IDs

## Parameters
- `channel_ids` (query): Comma separated list of up to 10 channel IDs e.g. neynar,farcaster
- `with_recasts` (query): Include recasts in the response, true by default
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `with_replies` (query): Include replies in the response, false by default
- `members_only` (query): Only include casts from members of the channel. True by default.
- `fids` (query): Comma separated list of FIDs to filter the feed by, up to 10 at a time
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.
- `should_moderate` (query): If true, only casts that have been liked by the moderator (if one exists) will be returned.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
