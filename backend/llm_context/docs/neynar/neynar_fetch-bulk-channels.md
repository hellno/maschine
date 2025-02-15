# fetch-bulk-channels

**Endpoint**: `GET /farcaster/channel/bulk`

## Description
Returns details of multiple channels

## Parameters
- `ids` (query): Comma separated list of channel IDs or parent_urls, up to 100 at a time
- `type` (query): Type of identifier being used to query the channels. Defaults to ID.
- `viewer_fid` (query): FID of the user viewing the channels.

## Response
```typescript
{'type': 'object', 'required': ['channels'], 'properties': {'channels': {'type': 'array', 'items': {'$ref': '#/components/schemas/Channel'}}}}
```
