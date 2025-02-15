# fetch-frame-catalog

**Endpoint**: `GET /farcaster/frame/catalog`

## Description
A curated list of featured frames

## Parameters
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor

## Response
```typescript
{'type': 'object', 'required': ['frames', 'next'], 'properties': {'frames': {'type': 'array', 'items': {'$ref': '#/components/schemas/FrameV2'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
