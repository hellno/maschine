# fetch-subscribed-to-for-fid

**Endpoint**: `GET /farcaster/user/subscribed_to`

## Description
Fetch what FIDs and contracts a FID is subscribed to.

## Parameters
- `fid` (query): No description
- `viewer_fid` (query): No description
- `subscription_provider` (query): No description

## Response
```yaml
type: object
properties:
  subscribed_to:
    type: array
    items:
      allOf:
      - type: object
        required:
        - object
        - contract_address
        - chain
        - metadata
        - owner_address
        - price
        - protocol_version
        - token
        properties:
          object:
            type: string
            examples:
            - subscription
          provider_name:
            type: string
            examples:
            - fabric_stp
          contract_address:
            type: string
            examples:
            - '0xff63fc310d47ef80961056ac8df0b3f1a9e3ef58'
          chain:
            type: integer
            examples:
            - 8453
          metadata:
            type: object
            properties:
              title:
                type: string
                examples:
                - /memes channel sub
              symbol:
                type: string
                examples:
                - MMS
              art_url:
                type: string
                examples:
                - https://storage.withfabric.xyz/loom/403fdc10-95f3-4b25-9d77-5aac7ccb9fd1.jpg
            required:
            - title
            - symbol
            - art_url
          owner_address:
            type: string
            examples:
            - '0xb6f6dce6000ca88cc936b450cedb16a5c15f157f'
          price:
            type: object
            properties:
              period_duration_seconds:
                type: integer
                examples:
                - 2592000
              tokens_per_period:
                type: string
                examples:
                - '350574998400000'
              initial_mint_price:
                type: string
                examples:
                - '0'
            required:
            - period_duration_seconds
            - tokens_per_period
            - initial_mint_price
          tiers:
            type: array
            items: &id001
              type: object
              properties:
                id:
                  type: integer
                  examples:
                  - 1
                price:
                  type: object
                  properties:
                    period_duration_seconds:
                      type: integer
                      examples:
                      - 2592000
                    tokens_per_period:
                      type: string
                      examples:
                      - '3000000000000000'
                    initial_mint_price:
                      type: string
                      examples:
                      - '0'
          protocol_version:
            type: integer
            examples:
            - 1
          token:
            type: object
            properties:
              symbol:
                type: string
                examples:
                - ETH
              address:
                type:
                - string
                - 'null'
                examples:
                - null
              decimals:
                type: integer
                examples:
                - 18
              erc20:
                type: boolean
                examples:
                - false
            required:
            - symbol
            - address
            - decimals
            - erc20
      - type: object
        required:
        - expires_at
        - subscribed_at
        - tier
        - creator
        properties:
          expires_at:
            type: string
            format: date-time
            examples:
            - '2023-09-13T22:10:22.000Z'
          subscribed_at:
            type: string
            format: date-time
            examples:
            - '2023-09-13T22:10:22.000Z'
          tier: *id001
          creator:
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
              custody_address: &id002
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
                items: *id002
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
                    items: *id002
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
                description: Adds context on the viewer's follow relationship with
                  the user.
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
```
