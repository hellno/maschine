# fetch-embedded-url-metadata

**Endpoint**: `GET /farcaster/cast/embed/crawl`

## Description
Crawls the given URL and returns metadata useful when embedding the URL in a cast.

## Parameters
- `url` (query): URL to crawl metadata of

## Response
```yaml
type: object
required:
- metadata
properties:
  metadata:
    type: object
    required:
    - _status
    properties:
      _status:
        type: string
      content_type:
        type:
        - string
        - 'null'
      content_length:
        type:
        - integer
        - 'null'
      image:
        type: object
        properties:
          height_px:
            type: integer
          width_px:
            type: integer
      video:
        type: object
        properties:
          duration_s:
            type: number
          stream:
            type: array
            items:
              type: object
              properties:
                codec_name:
                  type: string
                height_px:
                  type: integer
                width_px:
                  type: integer
      html:
        allOf:
        - type: object
          properties:
            favicon:
              type: string
            modifiedTime:
              type: string
            ogArticleAuthor:
              type: string
            ogArticleExpirationTime:
              type: string
            ogArticleModifiedTime:
              type: string
            ogArticlePublishedTime:
              type: string
            ogArticlePublisher:
              type: string
            ogArticleSection:
              type: string
            ogArticleTag:
              type: string
            ogAudio:
              type: string
            ogAudioSecureURL:
              type: string
            ogAudioType:
              type: string
            ogAudioURL:
              type: string
            ogAvailability:
              type: string
            ogDate:
              type: string
            ogDescription:
              type: string
            ogDeterminer:
              type: string
            ogEpisode:
              type: string
            ogImage:
              type: array
              items:
                type: object
                properties:
                  height:
                    type: string
                  type:
                    type: string
                  url:
                    type: string
                  width:
                    type: string
                  alt:
                    type: string
                required:
                - url
            ogLocale:
              type: string
            ogLocaleAlternate:
              type: string
            ogLogo:
              type: string
            ogMovie:
              type: string
            ogPriceAmount:
              type: string
            ogPriceCurrency:
              type: string
            ogProductAvailability:
              type: string
            ogProductCondition:
              type: string
            ogProductPriceAmount:
              type: string
            ogProductPriceCurrency:
              type: string
            ogProductRetailerItemId:
              type: string
            ogSiteName:
              type: string
            ogTitle:
              type: string
            ogType:
              type: string
            ogUrl:
              type: string
            ogVideo:
              type: array
              items:
                type: object
                properties:
                  height:
                    type: string
                  type:
                    type: string
                  url:
                    type: string
                  width:
                    type: string
                required:
                - url
            ogVideoActor:
              type: string
            ogVideoActorId:
              type: string
            ogVideoActorRole:
              type: string
            ogVideoDirector:
              type: string
            ogVideoDuration:
              type: string
            ogVideoOther:
              type: string
            ogVideoReleaseDate:
              type: string
            ogVideoSecureURL:
              type: string
            ogVideoSeries:
              type: string
            ogVideoTag:
              type: string
            ogVideoTvShow:
              type: string
            ogVideoWriter:
              type: string
            ogWebsite:
              type: string
            updatedTime:
              type: string
        - type: object
          properties:
            oembed:
              oneOf:
              - allOf:
                - &id001
                  type: object
                  description: Basic data structure of every oembed response see https://oembed.com/
                  required:
                  - type
                  - version
                  properties:
                    type:
                      type: string
                    version:
                      type:
                      - string
                      - 'null'
                    title:
                      type:
                      - string
                      - 'null'
                      description: A text title, describing the resource.
                    author_name:
                      type:
                      - string
                      - 'null'
                      description: The name of the author/owner of the resource.
                    author_url:
                      type:
                      - string
                      - 'null'
                      description: A URL for the author/owner of the resource.
                    provider_name:
                      type:
                      - string
                      - 'null'
                      description: The name of the resource provider.
                    provider_url:
                      type:
                      - string
                      - 'null'
                      description: The url of the resource provider.
                    cache_age:
                      type:
                      - string
                      - 'null'
                      description: The suggested cache lifetime for this resource,
                        in seconds. Consumers may choose to use this value or not.
                    thumbnail_url:
                      type:
                      - string
                      - 'null'
                      description: A URL to a thumbnail image representing the resource.
                        The thumbnail must respect any maxwidth and maxheight parameters.
                        If this parameter is present, thumbnail_width and thumbnail_height
                        must also be present.
                    thumbnail_width:
                      type:
                      - number
                      - 'null'
                      description: The width of the optional thumbnail. If this parameter
                        is present, thumbnail_url and thumbnail_height must also be
                        present.
                    thumbnail_height:
                      type:
                      - number
                      - 'null'
                      description: The height of the optional thumbnail. If this parameter
                        is present, thumbnail_url and thumbnail_width must also be
                        present.
                - type: object
                  required:
                  - type
                  - html
                  - width
                  - height
                  properties:
                    type:
                      type: string
                      enum:
                      - rich
                    html:
                      type:
                      - string
                      - 'null'
                      description: The HTML required to display the resource. The
                        HTML should have no padding or margins. Consumers may wish
                        to load the HTML in an off-domain iframe to avoid XSS vulnerabilities.
                        The markup should be valid XHTML 1.0 Basic.
                    width:
                      type:
                      - number
                      - 'null'
                      description: The width in pixels required to display the HTML.
                    height:
                      type:
                      - number
                      - 'null'
                      description: The height in pixels required to display the HTML.
              - allOf:
                - *id001
                - type: object
                  required:
                  - type
                  - html
                  - width
                  - height
                  properties:
                    type:
                      type: string
                      enum:
                      - video
                    html:
                      type:
                      - string
                      - 'null'
                      description: The HTML required to embed a video player. The
                        HTML should have no padding or margins. Consumers may wish
                        to load the HTML in an off-domain iframe to avoid XSS vulnerabilities.
                    width:
                      type:
                      - number
                      - 'null'
                      description: The width in pixels required to display the HTML.
                    height:
                      type:
                      - number
                      - 'null'
                      description: The height in pixels required to display the HTML.
              - allOf:
                - *id001
                - type: object
                  required:
                  - type
                  - url
                  - width
                  - height
                  properties:
                    type:
                      type: string
                      enum:
                      - photo
                    url:
                      type:
                      - string
                      - 'null'
                      description: The source URL of the image. Consumers should be
                        able to insert this URL into an <img> element. Only HTTP and
                        HTTPS URLs are valid.
                    width:
                      type:
                      - number
                      - 'null'
                      description: The width in pixels of the image specified in the
                        url parameter.
                    height:
                      type:
                      - number
                      - 'null'
                      description: The height in pixels of the image specified in
                        the url parameter.
              - allOf:
                - *id001
                - type: object
                  required:
                  - type
                  properties:
                    type:
                      type: string
                      enum:
                      - link
              discriminator:
                propertyName: type
                mapping:
                  rich: '#/components/schemas/OembedRichData'
                  video: '#/components/schemas/OembedVideoData'
                  photo: '#/components/schemas/OembedPhotoData'
                  link: '#/components/schemas/OembedLinkData'
      frame:
        discriminator:
          propertyName: version
        oneOf:
        - description: Frame v1 object
          allOf:
          - &id002
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
                      description: The action type of a frame button. Action types
                        "mint" & "link" are to be handled on the client side only
                        and so they will produce a no/op for POST /farcaster/frame/action.
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
                      description: Used specifically for the tx action type to post
                        a successful transaction hash
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
          - *id002
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
                    description: The unique identifier of a farcaster user (unsigned
                      integer)
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
