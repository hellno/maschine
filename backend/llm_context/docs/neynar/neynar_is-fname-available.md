# is-fname-available

**Endpoint**: `GET /farcaster/fname/availability`

## Description
Check if a given fname is available

## Parameters
- `fname` (query): No description

## Response
```yaml
type: object
required:
- available
properties:
  available:
    type: boolean
```
