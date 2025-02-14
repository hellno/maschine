# Search for casts on Farcaster via Neynar API

https://api.neynar.com/v2/farcaster/cast/search
Search for casts based on a query string, with optional AND filters

Searching Casts
You can search for casts using keywords and commands in the search query. The following search commands are supported:

Date Range Commands
before:YYYY-MM-DD - Find casts created before the specified date
after:YYYY-MM-DD - Find casts created after the specified date
For example:

star wars before:2023-01-01 - Find Star Wars-related casts from before 2023
blockchain after:2023-06-01 - Find blockchain-related casts from after June 2023
Query Params
q
string
required
Query string to search for casts. Include 'before:YYYY-MM-DD' or 'after:YYYY-MM-DD' to search for casts before or after a specific date.

author_fid
int32
Fid of the user whose casts you want to search

viewer_fid
int32
Providing this will return search results that respects this user's mutes and blocks and includes viewer_context.

parent_url
string
Parent URL of the casts you want to search

channel_id
string
Channel ID of the casts you want to search

priority_mode
boolean
Defaults to false
When true, only returns search results from power badge users and users that the viewer follows (if viewer_fid is provided).

false
limit
int32
1 to 100
Defaults to 25
Number of results to fetch

25
cursor
string
Pagination cursor

const url = 'https://api.neynar.com/v2/farcaster/cast/search?priority_mode=false&limit=25';
const options = {
method: 'GET',
headers: {accept: 'application/json', 'x-api-key': 'NEYNAR_API_DOCS'}
};

fetch(url, options)
.then(res => res.json())
.then(json => console.log(json))
.catch(err => console.error(err));

Response:
{ "result": { "casts": [ { "hash": "string", "parent_hash": "string", "parent_url": "string", "root_parent_url": "string", "parent_author": { "fid": 0 }, "author": { "object": "user", "fid": 3, "username": "string", "display_name": "string", "custody_address": "string", "pfp_url": "string", "profile": { "bio": { "text": "string", "mentioned_profiles": [ "string" ] }, "location": { "latitude": 0, "longitude": 0, "address": { "city": "string", "state": "string", "state_code": "string", "country": "string", "country_code": "string" } } }, "follower_count": 0, "following_count": 0, "verifications": [ "string" ], "verified_addresses": { "eth_addresses": [ "string" ], "sol_addresses": [ "string" ] }, "verified_accounts": [ { "platform": "x", "username": "string" } ], "power_badge": true, "experimental": { "neynar_user_score": 0 }, "viewer_context": { "following": true, "followed_by": true, "blocking": true, "blocked_by": true } }, "text": "string", "timestamp": "2025-02-14T18:58:33.704Z", "embeds": [ { "url": "string", "metadata": { "\_status": "string", "content_type": "string", "content_length": 0, "image": { "height_px": 0, "width_px": 0 }, "video": { "duration_s": 0, "stream": [ { "codec_name": "string", "height_px": 0, "width_px": 0 } ] }, "html": { "favicon": "string", "modifiedTime": "string", "ogArticleAuthor": "string", "ogArticleExpirationTime": "string", "ogArticleModifiedTime": "string", "ogArticlePublishedTime": "string", "ogArticlePublisher": "string", "ogArticleSection": "string", "ogArticleTag": "string", "ogAudio": "string", "ogAudioSecureURL": "string", "ogAudioType": "string", "ogAudioURL": "string", "ogAvailability": "string", "ogDate": "string", "ogDescription": "string", "ogDeterminer": "string", "ogEpisode": "string", "ogImage": [ { "height": "string", "type": "string", "url": "string", "width": "string", "alt": "string" } ], "ogLocale": "string", "ogLocaleAlternate": "string", "ogLogo": "string", "ogMovie": "string", "ogPriceAmount": "string", "ogPriceCurrency": "string", "ogProductAvailability": "string", "ogProductCondition": "string", "ogProductPriceAmount": "string", "ogProductPriceCurrency": "string", "ogProductRetailerItemId": "string", "ogSiteName": "string", "ogTitle": "string", "ogType": "string", "ogUrl": "string", "ogVideo": [ { "height": "string", "type": "string", "url": "string", "width": "string" } ], "ogVideoActor": "string", "ogVideoActorId": "string", "ogVideoActorRole": "string", "ogVideoDirector": "string", "ogVideoDuration": "string", "ogVideoOther": "string", "ogVideoReleaseDate": "string", "ogVideoSecureURL": "string", "ogVideoSeries": "string", "ogVideoTag": "string", "ogVideoTvShow": "string", "ogVideoWriter": "string", "ogWebsite": "string", "updatedTime": "string", "oembed": { "type": "rich", "version": "string", "title": "string", "author_name": "string", "author_url": "string", "provider_name": "string", "provider_url": "string", "cache_age": "string", "thumbnail_url": "string", "thumbnail_width": 0, "thumbnail_height": 0, "html": "string", "width": 0, "height": 0 } }, "frame": { "version": "string", "image": "string", "frames_url": "string", "buttons": [ { "title": "string", "index": 0, "action_type": "post", "target": "string", "post_url": "string" } ], "post_url": "string", "title": "string", "image_aspect_ratio": "string", "input": { "text": "string" }, "state": { "serialized": "string" } } } }, { "cast": { "hash": "string", "parent_hash": "string", "parent_url": "string", "root_parent_url": "string", "parent_author": { "fid": 0 }, "author": { "object": "user_dehydrated", "fid": 3, "username": "string", "display_name": "string", "pfp_url": "string" }, "text": "string", "timestamp": "2025-02-14T18:58:33.704Z", "type": "cast-mention", "embeds": [ { "url": "string", "metadata": { "\_status": "string", "content_type": "string", "content_length": 0, "image": { "height_px": 0, "width_px": 0 }, "video": { "duration_s": 0, "stream": [ { "codec_name": "string", "height_px": 0, "width_px": 0 } ] }, "html": { "favicon": "string", "modifiedTime": "string", "ogArticleAuthor": "string", "ogArticleExpirationTime": "string", "ogArticleModifiedTime": "string", "ogArticlePublishedTime": "string", "ogArticlePublisher": "string", "ogArticleSection": "string", "ogArticleTag": "string", "ogAudio": "string", "ogAudioSecureURL": "string", "ogAudioType": "string", "ogAudioURL": "string", "ogAvailability": "string", "ogDate": "string", "ogDescription": "string", "ogDeterminer": "string", "ogEpisode": "string", "ogImage": [ { "height": "string", "type": "string", "url": "string", "width": "string", "alt": "string" } ], "ogLocale": "string", "ogLocaleAlternate": "string", "ogLogo": "string", "ogMovie": "string", "ogPriceAmount": "string", "ogPriceCurrency": "string", "ogProductAvailability": "string", "ogProductCondition": "string", "ogProductPriceAmount": "string", "ogProductPriceCurrency": "string", "ogProductRetailerItemId": "string", "ogSiteName": "string", "ogTitle": "string", "ogType": "string", "ogUrl": "string", "ogVideo": [ { "height": "string", "type": "string", "url": "string", "width": "string" } ], "ogVideoActor": "string", "ogVideoActorId": "string", "ogVideoActorRole": "string", "ogVideoDirector": "string", "ogVideoDuration": "string", "ogVideoOther": "string", "ogVideoReleaseDate": "string", "ogVideoSecureURL": "string", "ogVideoSeries": "string", "ogVideoTag": "string", "ogVideoTvShow": "string", "ogVideoWriter": "string", "ogWebsite": "string", "updatedTime": "string", "oembed": { "type": "rich", "version": "string", "title": "string", "author_name": "string", "author_url": "string", "provider_name": "string", "provider_url": "string", "cache_age": "string", "thumbnail_url": "string", "thumbnail_width": 0, "thumbnail_height": 0, "html": "string", "width": 0, "height": 0 } }, "frame": { "version": "string", "image": "string", "frames_url": "string", "buttons": [ { "title": "string", "index": 0, "action_type": "post", "target": "string", "post_url": "string" } ], "post_url": "string", "title": "string", "image_aspect_ratio": "string", "input": { "text": "string" }, "state": { "serialized": "string" } } } }, { "cast": { "object": "cast_dehydrated", "hash": "string", "author": { "object": "user_dehydrated", "fid": 3, "username": "string", "display_name": "string", "pfp_url": "string" } } } ], "channel": { "id": "string", "name": "string", "object": "channel_dehydrated", "image_url": "string", "viewer_context": { "following": true, "role": "member" } } } } ], "type": "cast-mention", "frames": [ { "version": "string", "image": "string", "frames_url": "string", "buttons": [ { "title": "string", "index": 0, "action_type": "post", "target": "string", "post_url": "string" } ], "post_url": "string", "title": "string", "image_aspect_ratio": "string", "input": { "text": "string" }, "state": { "serialized": "string" } }, { "version": "string", "image": "string", "frames_url": "string", "manifest": { "account_association": { "header": "string", "payload": "string", "signature": "string" }, "frame": { "version": "0.0.0", "name": "string", "home_url": "string", "icon_url": "string", "image_url": "string", "button_title": "string", "splash_image_url": "string", "splash_background_color": "string", "webhook_url": "string" }, "triggers": [ { "type": "cast", "id": "string", "url": "string", "name": "string" }, { "type": "composer", "id": "string", "url": "string", "name": "string" } ] }, "author": { "object": "user_dehydrated", "fid": 3, "username": "string", "display_name": "string", "pfp_url": "string" } } ], "reactions": { "likes": [ { "fid": 3 } ], "recasts": [ { "fid": 3, "fname": "string" } ], "likes_count": 0, "recasts_count": 0 }, "replies": { "count": 0 }, "thread_hash": "string", "mentioned_profiles": [ { "object": "user", "fid": 3, "username": "string", "display_name": "string", "custody_address": "string", "pfp_url": "string", "profile": { "bio": { "text": "string", "mentioned_profiles": [ "string" ] }, "location": { "latitude": 0, "longitude": 0, "address": { "city": "string", "state": "string", "state_code": "string", "country": "string", "country_code": "string" } } }, "follower_count": 0, "following_count": 0, "verifications": [ "string" ], "verified_addresses": { "eth_addresses": [ "string" ], "sol_addresses": [ "string" ] }, "verified_accounts": [ { "platform": "x", "username": "string" } ], "power_badge": true, "experimental": { "neynar_user_score": 0 }, "viewer_context": { "following": true, "followed_by": true, "blocking": true, "blocked_by": true } } ], "channel": { "id": "string", "url": "string", "name": "string", "description": "string", "object": "channel", "created_at": 0, "follower_count": 0, "external_link": { "title": "string", "url": "string" }, "image_url": "string", "parent_url": "string", "lead": { "object": "user", "fid": 3, "username": "string", "display_name": "string", "custody_address": "string", "pfp_url": "string", "profile": { "bio": { "text": "string", "mentioned_profiles": [ "string" ] }, "location": { "latitude": 0, "longitude": 0, "address": { "city": "string", "state": "string", "state_code": "string", "country": "string", "country_code": "string" } } }, "follower_count": 0, "following_count": 0, "verifications": [ "string" ], "verified_addresses": { "eth_addresses": [ "string" ], "sol_addresses": [ "string" ] }, "verified_accounts": [ { "platform": "x", "username": "string" } ], "power_badge": true, "experimental": { "neynar_user_score": 0 }, "viewer_context": { "following": true, "followed_by": true, "blocking": true, "blocked_by": true } }, "moderator_fids": [ 0 ], "member_count": 0, "pinned_cast_hash": "0xfe90f9de682273e05b201629ad2338bdcd89b6be", "viewer_context": { "following": true, "role": "member" } }, "viewer_context": { "liked": true, "recasted": true }, "author_channel_context": { "following": true, "role": "member" } } ], "next": { "cursor": "string" } } }
