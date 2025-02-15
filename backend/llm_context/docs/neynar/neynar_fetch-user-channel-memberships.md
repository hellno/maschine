# fetch-user-channel-memberships

**Endpoint**: `GET /farcaster/user/memberships/list`

## Description
Returns a list of all channels with their details that an FID is a member of. Data may have a delay of up to 1 hour.

## Parameters
- `fid` (query): The FID of the user.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['members', 'next'], 'properties': {'members': {'type': 'array', 'items': {'$ref': '#/components/schemas/ChannelMember'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
