# fetch-user-balance

**Endpoint**: `GET /farcaster/user/balance`

## Description
Fetches the token balances of a user given their FID

## Parameters
- `fid` (query): FID of the user to fetch
- `networks` (query): Comma separated list of networks to fetch balances for. Currently, only "base" is supported.

## Response
```typescript
{'type': 'object', 'properties': {'user_balance': {'type': 'object', 'required': ['object', 'user', 'address_balances'], 'properties': {'object': {'type': 'string', 'enum': ['user_balance']}, 'user': {'$ref': '#/components/schemas/UserDehydrated'}, 'address_balances': {'type': 'array', 'items': {'$ref': '#/components/schemas/AddressBalance'}}}}}}
```
