# lookup-cast-conversation

**Endpoint**: `GET /farcaster/cast/conversation`

## Description
Gets all casts related to a conversation surrounding a cast by passing in a cast hash or Warpcast URL. Includes all the ancestors of a cast up to the root parent in a chronological order. Includes all direct_replies to the cast up to the reply_depth specified in the query parameter.

## Parameters
- `identifier` (query): Cast identifier (Its either a url or a hash)
- `type` (query): No description
- `reply_depth` (query): The depth of replies in the conversation that will be returned (default 2)
- `include_chronological_parent_casts` (query): Include all parent casts in chronological order
- `viewer_fid` (query): Providing this will return a conversation that respects this user's mutes and blocks and includes `viewer_context`.
- `sort_type` (query): Sort type for the ordering of descendants. Default is `chron`
- `fold` (query): Show conversation above or below the fold. Lower quality responses are hidden below the fold. Not passing in a value shows the full conversation without any folding.
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['conversation'], 'properties': {'conversation': {'type': 'object', 'required': ['cast'], 'properties': {'cast': {'$ref': '#/components/schemas/CastWithInteractionsAndConversations'}, 'chronological_parent_casts': {'type': 'array', 'items': {'$ref': '#/components/schemas/CastWithInteractions'}}}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
