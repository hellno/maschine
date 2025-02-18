# fetch-validate-frame-analytics

**Endpoint**: `GET /farcaster/frame/validate/analytics`

## Description
Fetch analytics for total-interactors, interactors, nteractions-per-cast and input-text.

## Parameters
- `frame_url` (query): No description
- `analytics_type` (query): No description
- `start` (query): No description
- `stop` (query): No description
- `aggregate_window` (query): Required for `analytics_type=interactions-per-cast`

## Response
```yaml
oneOf:
- type: object
  required:
  - interactors
  properties:
    interactors:
      type: array
      items:
        type: object
        required:
        - fid
        - username
        - interaction_count
        properties:
          fid: &id001
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
          interaction_count:
            type: number
- type: object
  required:
  - total_interactors
  properties:
    total_interactors:
      type: number
- type: object
  required:
  - interactions_per_cast
  properties:
    interactions_per_cast:
      type: array
      items:
        type: object
        required:
        - start
        - stop
        - time
        - interaction_count
        - cast_url
        properties:
          start:
            type: string
            format: date-time
          stop:
            type: string
            format: date-time
          time:
            type: string
            format: date-time
          interaction_count:
            type: number
          cast_url:
            type: string
            format: uri
- type: object
  required:
  - input_texts
  properties:
    input_texts:
      type: array
      items:
        type: object
        required:
        - fid
        - username
        - input_text
        properties:
          fid: *id001
          username:
            type: string
          input_text:
            type: string
```
