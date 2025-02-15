# fetch-webhooks

**Endpoint**: `GET /farcaster/webhook/list`

## Description
Fetch a list of webhooks associated to a user

## Response
```typescript
{'type': 'object', 'required': ['webhooks'], 'properties': {'webhooks': {'type': 'array', 'items': {'$ref': '#/components/schemas/Webhook'}}}}
```
