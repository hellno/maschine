# fetch-relevant-followers

**Endpoint**: `GET /farcaster/followers/relevant`

## Description
Returns a list of relevant followers for a specific FID. This usually shows on a profile as "X, Y and Z follow this user".

## Parameters
- `target_fid` (query): User who's profile you are looking at
- `viewer_fid` (query): The FID of the user to customize this response for. Providing this will also return a list of followers that respects this user's mutes and blocks and includes `viewer_context`.

## Response
```typescript
{'type': 'object', 'required': ['top_relevant_followers_hydrated', 'all_relevant_followers_dehydrated'], 'properties': {'top_relevant_followers_hydrated': {'type': 'array', 'items': {'$ref': '#/components/schemas/HydratedFollower'}}, 'all_relevant_followers_dehydrated': {'type': 'array', 'items': {'$ref': '#/components/schemas/DehydratedFollower'}}}}
```
