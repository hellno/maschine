# fetch-neynar-frames

**Endpoint**: `GET /farcaster/frame/list`

## Description
Fetch a list of frames made by the developer (identified by API key)

## Response
```yaml
type: array
items:
  type: object
  properties:
    uuid:
      type: string
      format: uuid
      description: Unique identifier for the frame.
    name:
      type: string
      description: Name of the frame.
    link:
      type: string
      format: uri
      description: Generated link for the frame's first page.
    pages:
      type: array
      items:
        type: object
        properties:
          uuid:
            type: string
            format: uuid
            description: Unique identifier for the page.
          version:
            type: string
            default: vNext
            examples:
            - vNext
            description: The version of the page schema.
          title:
            type: string
            examples:
            - Welcome to Neynar
            description: The title of the page.
          image:
            type: object
            properties:
              url:
                type: string
                format: uri
                examples:
                - https://i.imgur.com/qo2AzBf.jpeg
                description: The URL of the page's image.
              aspect_ratio:
                type: string
                description: The aspect ratio of the image.
                enum:
                - 1.91:1
                - '1:1'
            required:
            - url
            - aspect_ratio
          buttons:
            type: array
            items:
              type: object
              properties:
                title:
                  type: string
                  description: The title of the button.
                index:
                  type: integer
                  description: The index of the button, first button should have index
                    1 and so on.
                action_type:
                  type: string
                  description: The type of action that the button performs.
                  enum:
                  - post
                  - post_redirect
                  - mint
                  - link
                next_page:
                  oneOf:
                  - type: object
                    properties:
                      uuid:
                        type: string
                        format: uuid
                        description: The UUID of the next page.
                    required:
                    - uuid
                  - type: object
                    properties:
                      redirect_url:
                        type: string
                        format: uri
                        description: The URL to redirect to.
                    required:
                    - redirect_url
                  - type: object
                    properties:
                      mint_url:
                        type: string
                        description: The URL for minting, specific to the mint action.
                    required:
                    - mint_url
              required:
              - title
              - index
              - action_type
          input:
            type: object
            properties:
              text:
                type: object
                properties:
                  enabled:
                    type: boolean
                    default: false
                    description: Indicates if text input is enabled.
                  placeholder:
                    type: string
                    description: The placeholder text for the input.
                required:
                - enabled
        required:
        - uuid
        - title
        - version
        - image
    valid:
      type: boolean
      description: Indicates if the frame is valid.
  required:
  - uuid
  - name
  - pages
  - link
```
