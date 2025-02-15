# fetch-cast-metrics

**Endpoint**: `GET /farcaster/cast/metrics`

## Description
Fetches metrics casts matching a query

## Parameters
- `q` (query): Query string to search for casts
- `interval` (query): Interval of time for which to fetch metrics. Choices are `1d`, `7d`, `30d`
- `author_fid` (query): Fid of the user whose casts you want to search
- `channel_id` (query): Channel ID of the casts you want to search

## Response
```yaml
type: object
required:
- metrics
properties:
  metrics:
    type: array
    items:
      type: object
      required:
      - start
      - resolution_in_seconds
      - cast_count
      properties:
        start:
          type: string
          format: date-time
        resolution_in_seconds:
          type: integer
          format: int32
        cast_count:
          type: integer
          format: int32
```
