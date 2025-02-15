# search-user

**Endpoint**: `GET /farcaster/user/search`

## Description
Search for Usernames

## Parameters
- `q` (query): No description
- `viewer_fid` (query): Providing this will return search results that respects this user's mutes and blocks and includes `viewer_context`.
- `limit` (query): Number of users to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['result'], 'properties': {'result': {'type': 'object', 'required': ['users'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/SearchedUser'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}}}
```
