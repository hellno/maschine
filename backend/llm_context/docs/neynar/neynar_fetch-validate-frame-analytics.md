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
```typescript
{'oneOf': [{'$ref': '#/components/schemas/FrameValidateAnalyticsInteractors'}, {'$ref': '#/components/schemas/FrameValidateAnalyticsTotalInteractors'}, {'$ref': '#/components/schemas/FrameValidateAnalyticsInteractionsPerCast'}, {'$ref': '#/components/schemas/FrameValidateAnalyticsInputText'}]}
```
