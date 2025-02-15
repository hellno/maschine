# fetch-all-notifications

**Endpoint**: `GET /farcaster/notifications`

## Description
Returns a list of notifications for a specific FID.

## Parameters
- `fid` (query): FID of the user you you want to fetch notifications for. The response will respect this user's mutes and blocks.
- `type` (query): Notification type to fetch. Comma separated values of follows, recasts, likes, mentions, replies.
- `priority_mode` (query): When true, only returns notifications from power badge users and users that the viewer follows (if viewer_fid is provided).
- `cursor` (query): Pagination cursor.

## Response
```typescript
{'type': 'object', 'required': ['unseen_notifications_count', 'notifications', 'next'], 'properties': {'unseen_notifications_count': {'type': 'integer', 'format': 'int32'}, 'notifications': {'type': 'array', 'items': {'$ref': '#/components/schemas/Notification'}}, 'next': {'$ref': '#/components/schemas/NextCursor'}}}
```
