# fetch-notifications-by-parent-url-for-user

**Endpoint**: `GET /farcaster/notifications/parent_url`

## Description
Returns a list of notifications for a user in specific parent_urls

## Parameters
- `fid` (query): FID of the user you you want to fetch notifications for. The response will respect this user's mutes and blocks.
- `parent_urls` (query): Comma separated parent_urls
- `priority_mode` (query): When true, only returns notifications from power badge users and users that the viewer follows (if viewer_fid is provided).
- `cursor` (query): Pagination cursor.

## Response
```yaml
type: object
required:
- unseen_notifications_count
- notifications
- next
properties:
  unseen_notifications_count:
    type: integer
    format: int32
  notifications:
    type: array
    items:
      type: object
      required:
      - object
      - most_recent_timestamp
      - type
      - seen
      properties:
        object:
          type: string
        most_recent_timestamp:
          type: string
          format: date-time
        type:
          type: string
          enum:
          - follows
          - recasts
          - likes
          - mention
          - reply
          - quote
        seen:
          type: boolean
        follows:
          type: array
          items:
            type: object
            required:
            - object
            - user
            properties:
              object:
                type: string
                enum:
                - follow
              user: &id003
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
                  fid: &id002
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
                        description: List of verified Ethereum addresses of the user
                          sorted by oldest to most recent.
                        items: *id001
                      sol_addresses:
                        type: array
                        description: List of verified Solana addresses of the user
                          sorted by oldest to most recent.
                        items:
                          type: string
                          pattern: ^[1-9A-HJ-NP-Za-km-z]{32,44}$
                          description: Solana address
                  verified_accounts:
                    type: array
                    description: Verified accounts of the user on other platforms,
                      currently only X is supported.
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
                        description: Score that represents the probability that the
                          account is not spam.
                  viewer_context:
                    type: object
                    description: Adds context on the viewer's follow relationship
                      with the user.
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
        cast:
          allOf:
          - type: object
            required:
            - hash
            - parent_hash
            - parent_url
            - root_parent_url
            - parent_author
            - author
            - text
            - timestamp
            - embeds
            properties:
              hash:
                type: string
              parent_hash:
                type:
                - string
                - 'null'
              parent_url:
                type:
                - string
                - 'null'
              root_parent_url:
                type:
                - string
                - 'null'
              parent_author:
                type: object
                required:
                - fid
                properties:
                  fid:
                    oneOf:
                    - type: 'null'
                    - *id002
              author: *id003
              text:
                type: string
              timestamp: &id007
                type: string
                format: date-time
              embeds:
                type: array
                items:
                  oneOf:
                  - &id008
                    type: object
                    required:
                    - url
                    properties:
                      url:
                        type: string
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
                                    - &id004
                                      type: object
                                      description: Basic data structure of every oembed
                                        response see https://oembed.com/
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
                                          description: A text title, describing the
                                            resource.
                                        author_name:
                                          type:
                                          - string
                                          - 'null'
                                          description: The name of the author/owner
                                            of the resource.
                                        author_url:
                                          type:
                                          - string
                                          - 'null'
                                          description: A URL for the author/owner
                                            of the resource.
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
                                          description: The suggested cache lifetime
                                            for this resource, in seconds. Consumers
                                            may choose to use this value or not.
                                        thumbnail_url:
                                          type:
                                          - string
                                          - 'null'
                                          description: A URL to a thumbnail image
                                            representing the resource. The thumbnail
                                            must respect any maxwidth and maxheight
                                            parameters. If this parameter is present,
                                            thumbnail_width and thumbnail_height must
                                            also be present.
                                        thumbnail_width:
                                          type:
                                          - number
                                          - 'null'
                                          description: The width of the optional thumbnail.
                                            If this parameter is present, thumbnail_url
                                            and thumbnail_height must also be present.
                                        thumbnail_height:
                                          type:
                                          - number
                                          - 'null'
                                          description: The height of the optional
                                            thumbnail. If this parameter is present,
                                            thumbnail_url and thumbnail_width must
                                            also be present.
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
                                          description: The HTML required to display
                                            the resource. The HTML should have no
                                            padding or margins. Consumers may wish
                                            to load the HTML in an off-domain iframe
                                            to avoid XSS vulnerabilities. The markup
                                            should be valid XHTML 1.0 Basic.
                                        width:
                                          type:
                                          - number
                                          - 'null'
                                          description: The width in pixels required
                                            to display the HTML.
                                        height:
                                          type:
                                          - number
                                          - 'null'
                                          description: The height in pixels required
                                            to display the HTML.
                                  - allOf:
                                    - *id004
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
                                          description: The HTML required to embed
                                            a video player. The HTML should have no
                                            padding or margins. Consumers may wish
                                            to load the HTML in an off-domain iframe
                                            to avoid XSS vulnerabilities.
                                        width:
                                          type:
                                          - number
                                          - 'null'
                                          description: The width in pixels required
                                            to display the HTML.
                                        height:
                                          type:
                                          - number
                                          - 'null'
                                          description: The height in pixels required
                                            to display the HTML.
                                  - allOf:
                                    - *id004
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
                                          description: The source URL of the image.
                                            Consumers should be able to insert this
                                            URL into an <img> element. Only HTTP and
                                            HTTPS URLs are valid.
                                        width:
                                          type:
                                          - number
                                          - 'null'
                                          description: The width in pixels of the
                                            image specified in the url parameter.
                                        height:
                                          type:
                                          - number
                                          - 'null'
                                          description: The height in pixels of the
                                            image specified in the url parameter.
                                  - allOf:
                                    - *id004
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
                          frame: &id011
                            discriminator:
                              propertyName: version
                            oneOf:
                            - description: Frame v1 object
                              allOf:
                              - &id005
                                description: Frame base object used across all versions
                                type: object
                                required:
                                - version
                                - image
                                - frames_url
                                properties:
                                  version:
                                    type: string
                                    description: Version of the frame, 'next' for
                                      v2, 'vNext' for v1
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
                                          description: The action type of a frame
                                            button. Action types "mint" & "link" are
                                            to be handled on the client side only
                                            and so they will produce a no/op for POST
                                            /farcaster/frame/action.
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
                                          description: Used specifically for the tx
                                            action type to post a successful transaction
                                            hash
                                  post_url:
                                    type: string
                                    description: Post URL to take an action on this
                                      frame
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
                                        description: State for the frame in a serialized
                                          format
                            - description: Frame v2 object
                              allOf:
                              - *id005
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
                                  author: &id006
                                    type: object
                                    required:
                                    - object
                                    - fid
                                    properties:
                                      object:
                                        type: string
                                        enum:
                                        - user_dehydrated
                                      fid: *id002
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
                  - type: object
                    required:
                    - cast
                    properties:
                      cast_id: &id009
                        type: object
                        required:
                        - fid
                        - hash
                        properties:
                          fid: *id002
                          hash:
                            type: string
                      cast:
                        type: object
                        required:
                        - hash
                        - parent_hash
                        - parent_url
                        - root_parent_url
                        - parent_author
                        - author
                        - text
                        - timestamp
                        - type
                        - embeds
                        - channel
                        properties:
                          hash:
                            type: string
                          parent_hash:
                            type:
                            - string
                            - 'null'
                          parent_url:
                            type:
                            - string
                            - 'null'
                          root_parent_url:
                            type:
                            - string
                            - 'null'
                          parent_author:
                            type: object
                            required:
                            - fid
                            properties:
                              fid:
                                oneOf:
                                - type: 'null'
                                - *id002
                          author: *id006
                          text:
                            type: string
                          timestamp: *id007
                          type: &id010
                            type: string
                            enum:
                            - cast-mention
                            - cast-reply
                            description: 'The notification type of a cast.

                              '
                          embeds:
                            type: array
                            items:
                              oneOf:
                              - *id008
                              - type: object
                                required:
                                - cast
                                properties:
                                  cast_id: *id009
                                  cast: &id014
                                    type: object
                                    required:
                                    - object
                                    - hash
                                    properties:
                                      object:
                                        type: string
                                        enum:
                                        - cast_dehydrated
                                      hash:
                                        type: string
                                      author: *id006
                          channel:
                            oneOf:
                            - type: 'null'
                            - &id013
                              type: object
                              required:
                              - id
                              - name
                              - object
                              properties:
                                id:
                                  type: string
                                name:
                                  type: string
                                object:
                                  type: string
                                  enum:
                                  - channel_dehydrated
                                image_url:
                                  type: string
                                viewer_context: &id012
                                  description: Adds context on the viewer's or author's
                                    role in the channel.
                                  type: object
                                  required:
                                  - following
                                  properties:
                                    following:
                                      description: Indicates if the user is following
                                        the channel.
                                      type: boolean
                                    role:
                                      type: string
                                      description: The role of a channel member
                                      enum:
                                      - member
                                      - moderator
              type: *id010
          - type: object
            required:
            - reactions
            - replies
            - thread_hash
            - mentioned_profiles
            - channel
            properties:
              frames:
                type: array
                items: *id011
              reactions:
                type: object
                required:
                - likes
                - recasts
                - likes_count
                - recasts_count
                properties:
                  likes:
                    type: array
                    items:
                      type: object
                      required:
                      - fid
                      properties:
                        fid: *id002
                  recasts:
                    type: array
                    items:
                      type: object
                      required:
                      - fid
                      - fname
                      properties:
                        fid: *id002
                        fname:
                          type: string
                  likes_count:
                    type: integer
                    format: int32
                  recasts_count:
                    type: integer
                    format: int32
              replies:
                type: object
                required:
                - count
                properties:
                  count:
                    type: integer
                    format: int32
              thread_hash:
                type:
                - string
                - 'null'
              mentioned_profiles:
                type: array
                items: *id003
              channel:
                oneOf:
                - oneOf:
                  - type: object
                    required:
                    - id
                    - url
                    - object
                    properties:
                      id:
                        type: string
                      url:
                        type: string
                      name:
                        type: string
                      description:
                        type: string
                      object:
                        type: string
                        enum:
                        - channel
                      created_at:
                        description: Epoch timestamp in seconds.
                        type: number
                      follower_count:
                        description: Number of followers the channel has.
                        type: number
                      external_link:
                        type: object
                        description: Channel's external link.
                        properties:
                          title:
                            type: string
                          url:
                            type: string
                      image_url:
                        type: string
                      parent_url:
                        type: string
                        format: uri
                      lead: *id003
                      moderator_fids:
                        type: array
                        items: *id002
                      member_count:
                        type: integer
                        format: int32
                      moderator: *id003
                      pinned_cast_hash:
                        type: string
                        default: '0xfe90f9de682273e05b201629ad2338bdcd89b6be'
                        description: Cast Hash
                      hosts:
                        type: array
                        deprecated: true
                        items: *id003
                      viewer_context: *id012
                  - *id013
                  discriminator:
                    propertyName: object
                    mapping:
                      channel: '#/components/schemas/Channel'
                      dehydrated_channel: '#/components/schemas/DehydratedChannel'
                - type: 'null'
              viewer_context:
                type: object
                description: Adds context on interactions the viewer has made with
                  the cast.
                required:
                - liked
                - recasted
                properties:
                  liked:
                    description: Indicates if the viewer liked the cast.
                    type: boolean
                  recasted:
                    description: Indicates if the viewer recasted the cast.
                    type: boolean
              author_channel_context: *id012
        reactions:
          type: array
          items:
            type: object
            required:
            - object
            - cast
            - user
            properties:
              object:
                type: string
                enum:
                - likes
                - recasts
              cast: *id014
              user: *id003
        count:
          type: integer
          format: int32
          description: The number of notifications of this(follows, likes, recast)
            type bundled in a single notification.
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
