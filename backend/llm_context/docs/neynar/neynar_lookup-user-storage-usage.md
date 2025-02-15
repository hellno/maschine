# lookup-user-storage-usage

**Endpoint**: `GET /farcaster/storage/usage`

## Description
Fetches storage usage for a given user

## Parameters
- `fid` (query): No description

## Response
```typescript
{'type': 'object', 'properties': {'object': {'type': 'string', 'examples': ['storage_usage']}, 'user': {'$ref': '#/components/schemas/UserDehydrated'}, 'casts': {'$ref': '#/components/schemas/StorageObject'}, 'reactions': {'$ref': '#/components/schemas/StorageObject'}, 'links': {'$ref': '#/components/schemas/StorageObject'}, 'verified_addresses': {'$ref': '#/components/schemas/StorageObject'}, 'username_proofs': {'$ref': '#/components/schemas/StorageObject'}, 'signers': {'$ref': '#/components/schemas/StorageObject'}, 'total_active_units': {'type': 'integer', 'examples': [2]}}}
```
