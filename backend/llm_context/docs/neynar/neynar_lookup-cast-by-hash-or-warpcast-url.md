# lookup-cast-by-hash-or-warpcast-url

**Endpoint**: `GET /farcaster/cast`

## Description
Gets information about an individual cast by passing in a Warpcast web URL or cast hash

## Parameters
- `identifier` (query): Cast identifier (Its either a url or a hash)
- `type` (query): No description
- `viewer_fid` (query): adds viewer_context to cast object to show whether viewer has liked or recasted the cast.

## Response
```typescript
{'type': 'object', 'required': ['cast'], 'properties': {'cast': {'$ref': '#/components/schemas/CastWithInteractions'}}}
```
