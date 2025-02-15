# fetch-relevant-fungible-owners

**Endpoint**: `GET /farcaster/fungible/owner/relevant`

## Description
Fetch a list of relevant owners for a specific FID. This usually shows on a fungible asset page as "X, Y, Z and N others you know own this asset".

## Parameters
- `contract_address` (query): Contract address of the fungible asset
- `networks` (query): Comma separated list of networks to fetch balances for. Currently, only "base" is supported.
- `viewer_fid` (query): The FID of the user to customize this response for. Providing this will also return a list of owners that respects this user's mutes and blocks and includes `viewer_context`.

## Response
```typescript
{'type': 'object', 'required': ['top_relevant_fungible_owners_hydrated', 'all_relevant_fungible_owners_dehydrated'], 'properties': {'top_relevant_owners_hydrated': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}, 'all_relevant_owners_dehydrated': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}}}
```
