# fetch-users-by-location

**Endpoint**: `GET /farcaster/user/by_location`

## Description
Fetches a list of users given a location

## Parameters
- `latitude` (query): Latitude of the location
- `longitude` (query): Longitude of the location
- `viewer_fid` (query): FID of the user viewing the feed. Providing this will return a list of users that respects this user's mutes and blocks and includes `viewer_context`.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor

## Response
```typescript
{'type': 'object', 'required': ['users', 'next'], 'properties': {'users': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
