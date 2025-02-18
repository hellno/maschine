# fetch-power-users-lite

**Endpoint**: `GET /farcaster/user/power_lite`

## Description
Fetches power users and respond in a backwards compatible format to Warpcast's deprecated power badge endpoint.

## Parameters

## Response
```yaml
type: object
required:
- result
properties:
  result:
    type: object
    required:
    - fids
    properties:
      fids:
        type: array
        items:
          type: integer
          format: int32
          description: The unique identifier of a farcaster user (unsigned integer)
          examples:
          - 3
          - 191
          - 2
          - 194
          - 19960
        description: List of FIDs
```
