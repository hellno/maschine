# buy-storage

**Endpoint**: `POST /farcaster/storage/buy`

## Description

This api will help you rent units of storage for an year for a specific FID.
A storage unit lets you store 5000 casts, 2500 reactions and 2500 links.

## Response

```typescript
{'type': 'object', 'properties': {'total_active_units': {'type': 'integer', 'examples': [13]}, 'allocations': {'type': 'array', 'items': {'$ref': '#/components/schemas/StorageAllocation'}}}}
```
