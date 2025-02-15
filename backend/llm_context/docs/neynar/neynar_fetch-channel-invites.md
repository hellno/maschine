# fetch-channel-invites

**Endpoint**: `GET /farcaster/channel/member/invite/list`

## Description
Fetch a list of invites, either in a channel or for a user. If both are provided, open channel invite for that user is returned.

## Parameters
- `channel_id` (query): Channel ID for the channel being queried
- `invited_fid` (query): FID of the user being invited
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['invites'], 'properties': {'invites': {'type': 'array', 'items': {'$ref': '#/components/schemas/ChannelMemberInvite'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
