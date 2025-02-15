# fetch-validate-frame-list

**Endpoint**: `GET /farcaster/frame/validate/list`

## Description
Fetch a list of all the frames validated by a user

## Response
```typescript
{'type': 'object', 'required': ['frames'], 'properties': {'frames': {'type': 'array', 'items': {'type': 'string', 'format': 'uri'}}}}
```
