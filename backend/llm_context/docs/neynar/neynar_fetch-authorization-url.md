# fetch-authorization-url

**Endpoint**: `GET /farcaster/login/authorize`

## Description
Fetch authorization url (Fetched authorized url useful for SIWN login operation)

## Parameters
- `client_id` (query): No description
- `response_type` (query): No description

## Response
```yaml
type: object
required:
- authorization_url
properties:
  authorization_url:
    type: string
    format: uri
```
