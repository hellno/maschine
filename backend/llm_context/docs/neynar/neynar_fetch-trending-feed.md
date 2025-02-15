# fetch-trending-feed

**Endpoint**: `GET /farcaster/feed/trending`

## Description
Fetch trending casts or on the global feed or channels feeds. 7d time window available for channel feeds only.

## Parameters
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `time_window` (query): Time window for trending casts (7d window for channel feeds only)
- `channel_id` (query): Channel ID to filter trending casts. Less active channels might have no casts in the time window selected.
- `provider` (query): The provider of the trending casts feed.
- `provider_metadata` (query): provider_metadata is a URI-encoded stringified JSON object that can be used to pass additional metadata to the provider. Only available for mbd provider right now. See [here](https://docs.neynar.com/docs/feed-for-you-w-external-providers) on how to use.


## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
