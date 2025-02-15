# fetch-user-following

**Endpoint**: `GET /farcaster/following`

## Description
Fetch a list of users followed by a user. Can optionally include a viewer_fid and sort_type.

## Parameters
- `fid` (query): FID of the user whose following you want to fetch.
- `viewer_fid` (query): Providing this will return a list of users that respects this user's mutes and blocks and includes `viewer_context`.
- `sort_type` (query): Optional parameter to sort the users based on different criteria.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/HydratedFollower'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
