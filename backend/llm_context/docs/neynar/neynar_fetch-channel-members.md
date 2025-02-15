# fetch-channel-members

**Endpoint**: `GET /farcaster/channel/member/list`

## Description
Fetch a list of members in a channel

## Parameters
- `channel_id` (query): Channel ID for the channel being queried
- `fid` (query): FID of the user being queried. Specify this to check if a user is a member of the channel without paginating through all members.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['members', 'next'], 'properties': {'members': {'type': 'array', 'items': {'$ref': '#/components/schemas/ChannelMember'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
