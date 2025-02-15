# lookup-user-by-custody-address

**Endpoint**: `GET /farcaster/user/custody-address`

## Description
Lookup a user by custody-address

## Parameters
- `custody_address` (query): Custody Address associated with mnemonic

## Response
```typescript
{'type': 'object', 'required': ['user'], 'properties': {'user': {'$ref': '#/components/schemas/User'}}}
```
