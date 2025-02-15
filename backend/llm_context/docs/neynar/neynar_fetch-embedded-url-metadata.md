# fetch-embedded-url-metadata

**Endpoint**: `GET /farcaster/cast/embed/crawl`

## Description
Crawls the given URL and returns metadata useful when embedding the URL in a cast.

## Parameters
- `url` (query): URL to crawl metadata of

## Response
```typescript
{'type': 'object', 'required': ['metadata'], 'properties': {'metadata': {'$ref': '#/components/schemas/EmbedUrlMetadata'}}}
```
