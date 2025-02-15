# lookup-user-storage-usage

**Endpoint**: `GET /farcaster/storage/usage`

## Description
Fetches storage usage for a given user

## Parameters
- `fid` (query): No description

## Response
```yaml
type: object
properties:
  object:
    type: string
    examples:
    - storage_usage
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
  casts: &id001
    type: object
    properties:
      object:
        type: string
        examples:
        - storage
      used:
        type: integer
        examples:
        - 3659
      capacity:
        type: integer
        examples:
        - 10000
  reactions: *id001
  links: *id001
  verified_addresses: *id001
  username_proofs: *id001
  signers: *id001
  total_active_units:
    type: integer
    examples:
    - 2
```
