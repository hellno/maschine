# lookup-channel

**Endpoint**: `GET /farcaster/channel`

## Description
Returns details of a channel

## Parameters
- `id` (query): Channel ID for the channel being queried
- `type` (query): Type of identifier being used to query the channel. Defaults to ID.
- `viewer_fid` (query): FID of the user viewing the channel.

## Response
```typescript
{'type': 'object', 'required': ['channel'], 'properties': {'channel': {'$ref': '#/components/schemas/Channel'}}}
```
