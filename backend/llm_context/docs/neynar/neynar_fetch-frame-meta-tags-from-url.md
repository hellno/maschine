# fetch-frame-meta-tags-from-url

**Endpoint**: `GET /farcaster/frame/crawl`

## Description
Fetches the frame meta tags from the URL

## Parameters
- `url` (query): The frame URL to crawl

## Response
```typescript
{'type': 'object', 'description': 'The frame object containing the meta tags', 'required': ['frame'], 'properties': {'frame': {'$ref': '#/components/schemas/Frame'}}}
```
