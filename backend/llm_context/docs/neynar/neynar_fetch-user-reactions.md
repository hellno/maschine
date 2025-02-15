# fetch-user-reactions

**Endpoint**: `GET /farcaster/reactions/user`

## Description
Fetches reactions for a given user

## Parameters
- `fid` (query): No description
- `viewer_fid` (query): Providing this will return a list of reactions that respects this user's mutes and blocks and includes `viewer_context`.
- `type` (query): Type of reaction to fetch (likes or recasts or all)
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['reactions', 'next'], 'properties': {'reactions': {'type': 'array', 'items': {'$ref': '#/components/schemas/ReactionWithCastInfo'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
