# fetch-bulk-users-by-eth-or-sol-address

**Endpoint**: `GET /farcaster/user/bulk-by-address`

## Description
Fetches all users based on multiple Ethereum or Solana addresses.

Each farcaster user has a custody Ethereum address and optionally verified Ethereum or Solana addresses. This endpoint returns all users that have any of the given addresses as their custody or verified Ethereum or Solana addresses.

A custody address can be associated with only 1 farcaster user at a time but a verified address can be associated with multiple users.
You can pass in Ethereum and Solana addresses, comma separated, in the same request. The response will contain users associated with the given addresses.

## Parameters
- `addresses` (query): Comma separated list of Ethereum addresses, up to 350 at a time
- `address_types` (query): Customize which address types the request should search for. This is a comma-separated string that can include the following values: 'custody_address' and 'verified_address'. By default api returns both. To select multiple types, use a comma-separated list of these values.

- `viewer_fid` (query): No description

## Response
```typescript
{'type': 'object', 'additionalProperties': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}}
```
