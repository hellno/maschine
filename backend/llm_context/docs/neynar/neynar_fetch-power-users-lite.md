# fetch-power-users-lite

**Endpoint**: `GET /farcaster/user/power_lite`

## Description
Fetches power users and respond in a backwards compatible format to Warpcast's deprecated power badge endpoint.

## Parameters

## Response
```typescript
{'type': 'object', 'required': ['result'], 'properties': {'result': {'type': 'object', 'required': ['fids'], 'properties': {'fids': {'$ref': '#/components/schemas/Fids'}}}}}
```
