# fetch-cast-reactions

**Endpoint**: `GET /farcaster/reactions/cast`

## Description
Fetches reactions for a given cast

## Parameters
- `hash` (query): No description
- `types` (query): Customize which reaction types the request should search for. This is a comma-separated string that can include the following values: 'likes' and 'recasts'. By default api returns both. To select multiple types, use a comma-separated list of these values.

- `viewer_fid` (query): Providing this will return a list of reactions that respects this user's mutes and blocks and includes `viewer_context`.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['reactions', 'next'], 'properties': {'reactions': {'type': 'array', 'items': {'$ref': '#/components/schemas/ReactionForCast'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
