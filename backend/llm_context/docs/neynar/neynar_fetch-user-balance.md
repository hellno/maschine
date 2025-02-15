# fetch-user-balance

**Endpoint**: `GET /farcaster/user/balance`

## Description
Fetches the token balances of a user given their FID

## Parameters
- `fid` (query): FID of the user to fetch
- `networks` (query): Comma separated list of networks to fetch balances for. Currently, only "base" is supported.

## Response
```yaml
type: object
properties:
  user_balance:
    type: object
    required:
    - object
    - user
    - address_balances
    properties:
      object:
        type: string
        enum:
        - user_balance
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
      address_balances:
        type: array
        items:
          type: object
          description: The token balances associated with a wallet address
          required:
          - object
          - verified_address
          - token_balances
          properties:
            object:
              type: string
              enum:
              - address_balance
            verified_address:
              type: object
              required:
              - address
              - network
              properties:
                address:
                  type: string
                  description: The wallet address
                network:
                  type: string
                  description: A blockchain network e.g. "base"
                  enum:
                  - base
            token_balances:
              type: array
              items:
                type: object
                description: The token balance associated with a wallet address and
                  a network
                required:
                - object
                - token
                - balance
                properties:
                  object:
                    type: string
                    enum:
                    - token_balance
                  token:
                    type: object
                    required:
                    - object
                    - name
                    - symbol
                    properties:
                      object:
                        type: string
                        enum:
                        - token
                      name:
                        type: string
                        description: The token name e.g. "Ethereum"
                      symbol:
                        type: string
                        description: The token symbol e.g. "ETH"
                      address:
                        type: string
                        description: The contract address of the token (omitted for
                          native token)
                      decimals:
                        type: integer
                        description: The number of decimals the token uses
                  balance:
                    type: object
                    required:
                    - in_token
                    - in_usdc
                    properties:
                      in_token:
                        type: string
                        description: The balance in the token
                      in_usdc:
                        type: string
                        description: The balance in USDC
```
