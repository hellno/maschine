# lookup-user-storage-allocations

**Endpoint**: `GET /farcaster/storage/allocations`

## Description
Fetches storage allocations for a given user

## Parameters
- `fid` (query): No description

## Response
```yaml
type: object
properties:
  total_active_units:
    type: integer
    examples:
    - 13
  allocations:
    type: array
    items:
      type: object
      properties:
        object:
          type: string
          examples:
          - storage_allocation
        user:
          type: object
          required:
          - object
          - fid
          properties:
            object:
              type: string
              enum:
              - user_dehydrated
            fid:
              type: integer
              format: int32
              description: The unique identifier of a farcaster user (unsigned integer)
              examples:
              - 3
              - 191
              - 2
              - 194
              - 19960
            username:
              type: string
            display_name:
              type: string
            pfp_url:
              type: string
        units:
          type: integer
          examples:
          - 10
        expiry:
          type: string
          format: date-time
          examples:
          - '2024-10-08T22:03:49.000Z'
        timestamp:
          type: string
          format: date-time
          examples:
          - '2023-10-09T22:03:49.000Z'
```
