# fetch-followers-for-a-channel

**Endpoint**: `GET /farcaster/channel/followers`

## Description
Returns a list of followers for a specific channel. Max limit is 1000. Use cursor for pagination.

## Parameters
- `id` (query): Channel ID for the channel being queried
- `viewer_fid` (query): Providing this will return a list of followers that respects this user's mutes and blocks and includes `viewer_context`.
- `cursor` (query): Pagination cursor.
- `limit` (query): Number of followers to fetch

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
