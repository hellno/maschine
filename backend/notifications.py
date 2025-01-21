"""
Notification service for sending user notifications via Farcaster.
Handles Redis connection management and notification delivery with proper error handling.
"""

import os
import uuid
import time
import requests
import redis
from typing import Optional, Dict, Any
from pydantic import BaseModel


class FrameNotificationDetails(BaseModel):
    """Details required to send notifications to a user"""
    url: str
    token: str


class NotificationResult(BaseModel):
    """Result of a notification attempt"""
    state: str
    error: Optional[str] = None


class NotificationService:
    """Manages notification operations with proper connection handling and error recovery"""

    def __init__(self, frontend_url: Optional[str] = None):
        self.frontend_url = frontend_url or os.getenv(
            'FRONTEND_URL', 'https://farcasterframeception.vercel.app')
        self._redis_client = None

    def send_notification(self, fid: int, title: str, body: str) -> NotificationResult:
        """
        Send a notification to a user with proper error handling and logging.

        Args:
            fid: Farcaster ID of the recipient
            title: Notification title
            body: Notification body

        Returns:
            NotificationResult indicating success or failure state
        """
        try:
            print(f"Attempting to send notification to FID {
                  fid} with title: {title}")

            details = self._get_notification_details(fid)
            if not details:
                return NotificationResult(state="no_token")

            payload = self._build_notification_payload(
                title, body, details.token)
            result = self._send_notification_request(details.url, payload)

            self._handle_notification_response(result, fid, details.token)

            print(f"Successfully sent notification to FID {fid}")
            return NotificationResult(state="success")

        except Exception as e:
            error_msg = f"Unexpected error sending notification to FID {
                fid}: {str(e)}"
            print(error_msg)
            return NotificationResult(state="error", error=error_msg)

    def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client with proper connection handling"""
        if self._redis_client is None:
            redis_url = os.getenv(
                "KV_REST_API_URL", "").replace('https://', '')
            redis_token = os.getenv("KV_REST_API_TOKEN", "")

            if not redis_url or not redis_token:
                raise ValueError("Missing Redis credentials")

            self._redis_client = redis.Redis(
                host=redis_url,
                password=redis_token,
                port=6379,
                ssl=True,
                decode_responses=True
            )
        return self._redis_client

    def _get_notification_details(self, fid: int) -> Optional[FrameNotificationDetails]:
        """Retrieve notification details for a user from Redis"""
        try:
            redis_client = self._get_redis_client()
            data = redis_client.get(self._get_details_key(fid))
            return FrameNotificationDetails.parse_raw(data) if data else None
        except Exception as e:
            print(f"Error getting notification details: {str(e)}")
            return None

    def _build_notification_payload(self, title: str, body: str, token: str) -> Dict[str, Any]:
        """Build the notification payload with proper structure"""
        return {
            "notificationId": str(uuid.uuid4()),
            "title": title,
            "body": body,
            "targetUrl": self.frontend_url,
            "tokens": [token]
        }

    def _send_notification_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification request with proper error handling"""
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _handle_notification_response(self, result: Dict[str, Any], fid: int, token: str) -> None:
        """Handle notification response and cleanup invalid tokens"""
        result_data = result.get("result", {})

        if token in result_data.get("invalidTokens", []):
            print(f"Invalid token found for FID {fid}, cleaning up")
            self._delete_notification_details(fid)

        if token in result_data.get("rateLimitedTokens", []):
            print(f"Rate limit hit for FID {fid}")

    def _delete_notification_details(self, fid: int) -> None:
        """Delete notification details for a user"""
        try:
            redis_client = self._get_redis_client()
            redis_client.delete(self._get_details_key(fid))
        except Exception as e:
            print(f"Error deleting notification details: {str(e)}")

    @staticmethod
    def _get_details_key(fid: int) -> str:
        """Generate Redis key for user notification details"""
        return f"frameception:{fid}:notifications"


# Create singleton instance for use in Modal functions


def send_notification(fid: int, title: str, body: str) -> Dict[str, Any]:
    """
    Convenience function for sending notifications from Modal functions.
    Maintains backward compatibility with existing code.
    """
    notification_service = NotificationService()
    result = notification_service.send_notification(fid, title, body)
    return {"state": result.state, "error": result.error}
