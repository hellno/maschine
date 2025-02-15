# fetch-feed

**Endpoint**: `GET /farcaster/feed`

## Description
Fetch casts based on filters. Ensure setting the correct parameters based on the feed_type and filter_type.

## Parameters
- `feed_type` (query): Defaults to following (requires FID or address). If set to filter (requires filter_type)
- `filter_type` (query): Used when feed_type=filter. Can be set to FIDs (requires FIDs) or parent_url (requires parent_url) or channel_id (requires channel_id)
- `fid` (query): (Optional) FID of user whose feed you want to create. By default, the API expects this field, except if you pass a filter_type
- `fids` (query): Used when filter_type=FIDs . Create a feed based on a list of FIDs. Max array size is 100. Requires feed_type and filter_type.
- `parent_url` (query): Used when filter_type=parent_url can be used to fetch content under any parent url e.g. FIP-2 channels on Warpcast. Requires feed_type and filter_type
- `channel_id` (query): Used when filter_type=channel_id can be used to fetch casts under a channel. Requires feed_type and filter_type.
- `members_only` (query): Used when filter_type=channel_id. Only include casts from members of the channel. True by default.
- `embed_url` (query): Used when filter_type=embed_url can be used to fetch all casts with an embed url that contains embed_url. Requires feed_type and filter_type
- `embed_types` (query): Used when filter_type=embed_types can be used to fetch all casts with matching content types. Requires feed_type and filter_type
- `with_recasts` (query): Include recasts in the response, true by default
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.

## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
