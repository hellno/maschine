# lookup-neynar-frame

**Endpoint**: `GET /farcaster/frame`

## Description
Fetch a frame either by UUID or Neynar URL

## Parameters
- `type` (query): No description
- `uuid` (query): UUID of the frame to fetch
- `url` (query): URL of the Neynar frame to fetch

## Response
```typescript
{'type': 'object', 'properties': {'uuid': {'type': 'string', 'format': 'uuid', 'description': 'Unique identifier for the frame.'}, 'name': {'type': 'string', 'description': 'Name of the frame.'}, 'link': {'type': 'string', 'format': 'uri', 'description': "Generated link for the frame's first page."}, 'pages': {'type': 'array', 'items': {'$ref': '#/components/schemas/NeynarFramePage'}}, 'valid': {'type': 'boolean', 'description': 'Indicates if the frame is valid.'}}, 'required': ['uuid', 'name', 'pages', 'link']}
```
