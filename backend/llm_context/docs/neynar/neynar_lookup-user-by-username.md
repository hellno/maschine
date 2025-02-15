# lookup-user-by-username

**Endpoint**: `GET /farcaster/user/by_username`

## Description
Fetches a single hydrated user object given a username

## Parameters
- `username` (query): Username of the user to fetch
- `viewer_fid` (query): No description

## Response
```typescript
{'type': 'object', 'required': ['user'], 'properties': {'user': {'$ref': '#/components/schemas/User'}}}
```
