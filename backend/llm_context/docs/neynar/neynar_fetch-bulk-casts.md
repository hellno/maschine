# fetch-bulk-casts

**Endpoint**: `GET /farcaster/casts`

## Description
Fetch multiple casts using their respective hashes.

## Parameters
- `casts` (query): Hashes of the cast to be retrived (Comma separated, no spaces)
- `viewer_fid` (query): adds viewer_context to cast object to show whether viewer has liked or recasted the cast.
- `sort_type` (query): Optional parameter to sort the casts based on different criteria

## Response
```typescript
{'type': 'object', 'required': ['result'], 'properties': {'result': {'type': 'object', 'required': ['casts'], 'properties': {'casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}}}}}
```
