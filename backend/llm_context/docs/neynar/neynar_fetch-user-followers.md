# fetch-user-followers

**Endpoint**: `GET /farcaster/followers`

## Description
Returns a list of followers for a specific FID.

## Parameters
- `fid` (query): User who's profile you are looking at
- `viewer_fid` (query): Providing this will return a list of followers that respects this user's mutes and blocks and includes `viewer_context`.
- `sort_type` (query): Sort type for fetch followers. Default is `desc_chron`
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/HydratedFollower'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
