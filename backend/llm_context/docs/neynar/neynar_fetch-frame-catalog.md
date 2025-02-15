# fetch-frame-catalog

**Endpoint**: `GET /farcaster/frame/catalog`

## Description
A curated list of featured frames

## Parameters
- `limit` (query): Number of results to fetch
- `cursor` (query): Pagination cursor

## Response
```yaml
type: object
required:
- frames
- next
properties:
  frames:
    type: array
    items:
      description: Frame v2 object
      allOf:
      - description: Frame base object used across all versions
        type: object
        required:
        - version
        - image
        - frames_url
        properties:
          version:
            type: string
            description: Version of the frame, 'next' for v2, 'vNext' for v1
          image:
            type: string
            description: URL of the image
          frames_url:
            type: string
            description: Launch URL of the frame
      - type: object
        required:
        - title
        - name
        - icon
        properties:
          manifest:
            type: object
            properties:
              account_association:
                type: object
                properties:
                  header:
                    type: string
                  payload:
                    type: string
                  signature:
                    type: string
                required:
                - header
                - payload
                - signature
              frame:
                type: object
                properties:
                  version:
                    type: string
                    enum:
                    - 0.0.0
                    - 0.0.1
                    - '1'
                    - next
                  name:
                    type: string
                    maxLength: 32
                  home_url:
                    type: string
                    maxLength: 512
                  icon_url:
                    type: string
                    maxLength: 512
                  image_url:
                    type: string
                    maxLength: 512
                  button_title:
                    type: string
                    maxLength: 32
                  splash_image_url:
                    type: string
                    maxLength: 512
                  splash_background_color:
                    type: string
                  webhook_url:
                    type: string
                    maxLength: 512
                required:
                - version
                - name
                - home_url
                - icon_url
              triggers:
                type: array
                items:
                  oneOf:
                  - type: object
                    properties:
                      type:
                        type: string
                        enum:
                        - cast
                      id:
                        type: string
                      url:
                        type: string
                        maxLength: 512
                      name:
                        type: string
                        maxLength: 32
                    required:
                    - type
                    - id
                    - url
                  - type: object
                    properties:
                      type:
                        type: string
                        enum:
                        - composer
                      id:
                        type: string
                      url:
                        type: string
                        maxLength: 512
                      name:
                        type: string
                        maxLength: 32
                    required:
                    - type
                    - id
                    - url
            required:
            - account_association
          author:
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
