# fetch-notification-tokens

**Endpoint**: `GET /farcaster/frame/notification_tokens`

## Description
Returns a list of notifications tokens related for an app


## Parameters
- `limit` (query): Number of results to fetch
- `fids` (query): Comma separated list of FIDs, up to 100 at a time

## Response
```yaml
type: object
required:
- notification_tokens
- next
properties:
  notification_tokens:
    type: array
    items:
      type: object
      properties:
        object:
          type: string
          enum:
          - notification_token
        url:
          type: string
        token:
          type: string
        status:
          type: string
          enum:
          - enabled
          - disabled
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
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
  next:
    type: object
    description: Returns next cursor
    required:
    - cursor
    properties:
      cursor:
        type:
        - string
        - 'null'
```
