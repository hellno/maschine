# fetch-feed-for-you

**Endpoint**: `GET /farcaster/feed/for_you`

## Description
Fetch a personalized For You feed for a user

## Parameters
- `fid` (query): FID of user whose feed you want to create
- `viewer_fid` (query): Providing this will return a feed that respects this user's mutes and blocks and includes `viewer_context`.
- `provider` (query): No description
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.
- `provider_metadata` (query): provider_metadata is a URI-encoded stringified JSON object that can be used to pass additional metadata to the provider. Only available for mbd provider right now. See [here](https://docs.neynar.com/docs/feed-for-you-w-external-providers) on how to use.


## Response
```typescript
{'type': 'object', 'required': ['casts', 'next'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
