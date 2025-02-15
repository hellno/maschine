# fetch-block-list

**Endpoint**: `GET /farcaster/block/list`

## Description
Fetches all FIDs that a user has blocked or has been blocked by

## Parameters
- `blocker_fid` (query): Providing this will return the users that this user has blocked
- `blocked_fid` (query): Providing this will return the users that have blocked this user
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor.

## Response
```yaml
type: object
required:
- blocks
- next
properties:
  blocks:
    type: array
    items:
      type: object
      required:
      - object
      - timestamp
      - blocked_at
      properties:
        object:
          type: string
          enum:
          - block
        blocked: &id002
          type: object
          required:
          - object
          - fid
          - custody_address
          - username
          - profile
          - follower_count
          - following_count
          - verifications
          - verified_addresses
          - verified_accounts
          - power_badge
          properties:
            object:
              type: string
              enum:
              - user
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
            custody_address: &id001
              type: string
              pattern: ^0x[a-fA-F0-9]{40}$
              description: Ethereum address
            pfp_url:
              type: string
              description: The URL of the user's profile picture
            profile:
              type: object
              required:
              - bio
              properties:
                bio:
                  type: object
                  required:
                  - text
                  - mentioned_profiles
                  properties:
                    text:
                      type: string
                    mentioned_profiles:
                      type: array
                      items:
                        type: string
                      default: []
                location:
                  description: Coordinates and place names for a location
                  type: object
                  required:
                  - latitude
                  - longitude
                  properties:
                    latitude:
                      type: number
                      format: double
                      minimum: -90
                      maximum: 90
                    longitude:
                      type: number
                      format: double
                      minimum: -180
                      maximum: 180
                    address:
                      type: object
                      required:
                      - city
                      - country
                      properties:
                        city:
                          type: string
                        state:
                          type: string
                        state_code:
                          type: string
                        country:
                          type: string
                        country_code:
                          type: string
            follower_count:
              type: integer
              format: int32
              description: The number of followers the user has.
            following_count:
              type: integer
              format: int32
              description: The number of users the user is following.
            verifications:
              type: array
              items: *id001
            verified_addresses:
              type: object
              required:
              - eth_addresses
              - sol_addresses
              properties:
                eth_addresses:
                  type: array
                  description: List of verified Ethereum addresses of the user sorted
                    by oldest to most recent.
                  items: *id001
                sol_addresses:
                  type: array
                  description: List of verified Solana addresses of the user sorted
                    by oldest to most recent.
                  items:
                    type: string
                    pattern: ^[1-9A-HJ-NP-Za-km-z]{32,44}$
                    description: Solana address
            verified_accounts:
              type: array
              description: Verified accounts of the user on other platforms, currently
                only X is supported.
              items:
                type: object
                properties:
                  platform:
                    type: string
                    enum:
                    - x
                    - github
                  username:
                    type: string
            power_badge:
              type: boolean
            experimental:
              type: object
              required:
              - neynar_user_score
              properties:
                neynar_user_score:
                  type: number
                  format: double
                  description: Score that represents the probability that the account
                    is not spam.
            viewer_context:
              type: object
              description: Adds context on the viewer's follow relationship with the
                user.
              required:
              - following
              - followed_by
              - blocking
              - blocked_by
              properties:
                following:
                  description: Indicates if the viewer is following the user.
                  type: boolean
                followed_by:
                  description: Indicates if the viewer is followed by the user.
                  type: boolean
                blocking:
                  description: Indicates if the viewer is blocking the user.
                  type: boolean
                blocked_by:
                  description: Indicates if the viewer is blocked by the user.
                  type: boolean
        blocker: *id002
        blocked_at:
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
