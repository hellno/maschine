import os
import uuid
import time
import requests
import redis
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError, Field
from typing import Optional, List

app = FastAPI()

KV_REST_API_URL = os.getenv("KV_REST_API_URL", "")
KV_REST_API_TOKEN = os.getenv("KV_REST_API_TOKEN", "")
FRONTEND_URL = os.getenv('FRONTEND_URL', 'farcasterframeception.vercel.app')


r = redis.Redis(
    host=KV_REST_API_URL.replace('https://', ''),
    password=KV_REST_API_TOKEN,
    port=6379,
    ssl=True,
    decode_responses=True
)


class FrameNotificationDetails(BaseModel):
    url: str
    token: str


class SendNotificationRequest(BaseModel):
    notificationId: str
    title: str
    body: str
    targetUrl: str
    tokens: List[str]


class SendNotificationResponse(BaseModel):
    result: dict


class RequestSchema(BaseModel):
    fid: int
    notificationDetails: FrameNotificationDetails


def get_user_notification_details_key(fid: int) -> str:
    return f"frameception:{fid}:notifications"


def get_user_notification_details(fid: int) -> Optional[FrameNotificationDetails]:
    data = r.get(get_user_notification_details_key(fid))
    if not data:
        return None
    try:
        # Redis returns string; parse into FrameNotificationDetails
        return FrameNotificationDetails.parse_raw(data)
    except:
        return None


def set_user_notification_details(fid: int, details: FrameNotificationDetails) -> None:
    r.set(get_user_notification_details_key(fid), details.json())


def delete_user_notification_details(fid: int) -> None:
    r.delete(get_user_notification_details_key(fid))


def send_notification(fid: int, title: str, body: str) -> dict:
    """Send a notification to a user

    Args:
        fid: The user's Farcaster ID
        title: The notification title
        body: The notification body

    Returns:
        dict with state of notification attempt
    """
    print(f"Attempting to send notification to FID {fid} with title: {title}")
    try:
        # Get notification details from Redis
        details = get_user_notification_details(fid)
        if not details:
            print(f"No notification details found for FID {fid}")
            return {"state": "no_token"}

        # Prepare notification payload
        payload = {
            "notificationId": str(uuid.uuid4()),
            "title": title,
            "body": body,
            "targetUrl": FRONTEND_URL,
            "tokens": [details.token]
        }
        print(f"Sending notification payload: {payload}")

        try:
            response = requests.post(
                details.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            print(f"Notification response: {result}")

            # Check for invalid tokens
            if details.token in result.get("result", {}).get("invalidTokens", []):
                print(f"Invalid token found for FID {fid}, cleaning up")
                delete_user_notification_details(fid)
                return {"state": "invalid_token"}

            # Check for rate limits
            if details.token in result.get("result", {}).get("rateLimitedTokens", []):
                print(f"Rate limit hit for FID {fid}")
                return {"state": "rate_limit"}

            print(f"Successfully sent notification to FID {fid}")
            return {"state": "success"}

        except requests.exceptions.RequestException as e:
            print(f"Request error sending notification to FID {fid}: {str(e)}")
            return {"state": "error", "error": str(e)}

    except Exception as e:
        print(f"Unexpected error sending notification to FID {fid}: {str(e)}")
        return {"state": "error", "error": str(e)}
