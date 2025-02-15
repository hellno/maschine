# fetch-channel-notifications-for-user

**Endpoint**: `GET /farcaster/notifications/channel`

## Description
Returns a list of notifications for a user in specific channels

## Parameters
- `fid` (query): FID of the user you you want to fetch notifications for. The response will respect this user's mutes and blocks.
- `channel_ids` (query): Comma separated channel_ids (find list of all channels here - https://docs.neynar.com/reference/list-all-channels)
- `priority_mode` (query): When true, only returns notifications from power badge users and users that the viewer follows (if viewer_fid is provided).
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['unseen_notifications_count', 'notifications', 'next'], 'properties': {'unseen_notifications_count': {'type': 'integer', 'format': 'int32'}, 'notifications': {'type': 'array', 'items': {'$ref': '#/components/schemas/Notification'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
