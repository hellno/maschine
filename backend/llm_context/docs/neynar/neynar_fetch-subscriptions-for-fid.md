# fetch-subscriptions-for-fid

**Endpoint**: `GET /farcaster/user/subscriptions_created`

## Description
Fetch created subscriptions for a given FID's.

## Parameters
- `fid` (query): No description
- `subscription_provider` (query): No description

## Response
```yaml
type: object
properties:
  subscriptions_created:
    type: array
    items:
      type: object
      required:
      - object
      - subscriptions_created
      properties:
        object:
          type: string
        subscriptions_created:
          type: array
          items:
            type: object
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
                items:
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
```
