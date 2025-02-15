# fetch-frame-meta-tags-from-url

**Endpoint**: `GET /farcaster/frame/crawl`

## Description
Fetches the frame meta tags from the URL

## Parameters
- `url` (query): The frame URL to crawl

## Response
```yaml
type: object
description: The frame object containing the meta tags
required:
- frame
properties:
  frame:
    discriminator:
      propertyName: version
    oneOf:
    - description: Frame v1 object
      allOf:
      - &id001
        description: Frame base object used across all versions
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
        properties:
          buttons:
            type: array
            items:
              type: object
              required:
              - index
              - action_type
              properties:
                title:
                  type: string
                  description: Title of the button
                index:
                  type: integer
                  description: Index of the button
                action_type:
                  type: string
                  description: The action type of a frame button. Action types "mint"
                    & "link" are to be handled on the client side only and so they
                    will produce a no/op for POST /farcaster/frame/action.
                  enum:
                  - post
                  - post_redirect
                  - tx
                  - link
                  - mint
                target:
                  type: string
                  description: Target of the button
                post_url:
                  type: string
                  description: Used specifically for the tx action type to post a
                    successful transaction hash
          post_url:
            type: string
            description: Post URL to take an action on this frame
          title:
            type: string
          image_aspect_ratio:
            type: string
          input:
            type: object
            properties:
              text:
                type: string
                description: Input text for the frame
          state:
            type: object
            properties:
              serialized:
                type: string
                description: State for the frame in a serialized format
    - description: Frame v2 object
      allOf:
      - *id001
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
    mapping:
      vNext: '#/components/schemas/FrameV1'
      next: '#/components/schemas/FrameV2'
      '1': '#/components/schemas/FrameV2'
      0.0.0: '#/components/schemas/FrameV2'
      0.0.1: '#/components/schemas/FrameV2'
```
