# lookup-user-storage-allocations

**Endpoint**: `GET /farcaster/storage/allocations`

## Description
Fetches storage allocations for a given user

## Parameters
- `fid` (query): No description

## Response
```typescript
{'type': 'object', 'properties': {'total_active_units': {'type': 'integer', 'examples': [13]}, 'allocations': {'type': 'array', 'items': {'$ref': '#/components/schemas/StorageAllocation'}}}}
```
