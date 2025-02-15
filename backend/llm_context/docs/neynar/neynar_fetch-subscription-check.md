# fetch-subscription-check

**Endpoint**: `GET /stp/subscription_check`

## Description
Check if a wallet address is subscribed to a given STP (Hypersub) contract.

## Parameters
- `addresses` (query): Comma separated list of Ethereum addresses, up to 350 at a time
- `contract_address` (query): Ethereum address of the STP contract
- `chain_id` (query): Chain ID of the STP contract

## Response
```typescript
{'type': 'object', 'additionalProperties': {'$ref': '#/components/schemas/SubscriptionStatus'}, 'examples': [{'summary': 'Active subscription example', 'value': {'0xedd3783e8c7c52b80cfbd026a63c207edc9cbee7': {'object': 'subscribed_to_dehydrated', 'status': True, 'expires_at': 1748890497000, 'subscribed_at': 1719256819704, 'tier': {'id': 1, 'price': {'period_duration_seconds': 2592000, 'tokens_per_period': '3499999997472000', 'initial_mint_price': '0'}}}}}, {'summary': 'Inactive subscription example', 'value': {'0x5a927ac639636e534b678e81768ca19e2c6280b7': {'object': 'subscribed_to_dehydrated', 'status': False, 'expires_at': None, 'subscribed_at': None, 'tier': None}}}]}
```
