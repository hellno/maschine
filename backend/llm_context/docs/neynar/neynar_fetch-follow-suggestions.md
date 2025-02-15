# fetch-follow-suggestions

**Endpoint**: `GET /farcaster/following/suggested`

## Description
Fetch a list of suggested users to follow. Used to help users discover new users to follow

## Parameters
- `fid` (query): FID of the user whose following you want to fetch.
- `viewer_fid` (query): Providing this will return a list of users that respects this user's mutes and blocks and includes `viewer_context`.
- `limit` (query): Number of results to fetch

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
