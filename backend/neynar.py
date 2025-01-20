import requests
from typing import List, Dict, Optional
import os


def get_author_display(author: Dict) -> str:
    """Extract author display name and username safely"""
    display_name = author.get('display_name', 'Anonymous')
    username = author.get('username', 'unknown')
    return f"{display_name} (@{username})"


def get_location_string(author: Dict) -> str:
    """Safely extract and format location information"""
    try:
        profile = author.get('profile', {})
        location = profile.get('location', {}).get('address', {})
        city = location.get('city')
        country = location.get('country')

        if city and country:
            return f" from {city}, {country}"
    except Exception:
        pass
    return ""


def get_channel_string(cast_data: Dict) -> str:
    """Safely extract and format channel information"""
    try:
        channel = cast_data.get('channel', {}).get('name')
        return f" in #{channel}" if channel else ""
    except Exception:
        return ""


def get_follower_string(author: Dict) -> str:
    """Safely extract and format follower count"""
    try:
        follower_count = author.get('follower_count', 0)
        return f" (has {follower_count:,} followers)"
    except Exception:
        return ""


def get_user_casts(fid: int, nr_casts: int) -> List[dict]:
    url = f"https://api.neynar.com/v2/farcaster/feed?feed_type=filter&filter_type=fids&fids={
        fid}&with_recasts=false&limit={nr_casts}"

    headers = {
        "accept": "application/json",
        "x-api-key": os.environ["NEYNAR_API_KEY"],
    }

    response = requests.get(url, headers=headers)
    return response.json().get('casts')


def format_cast(cast: dict) -> Optional[str]:
    """
    Format a single cast into a readable string with improved error handling and logging
    Args:
        cast: Dictionary containing cast data from Neynar API
    Returns:
        Optional[str]: Formatted cast string or None if formatting fails
    """
    try:
        # Extract basic cast info
        text = cast.get('text')
        if not text:
            print("No text found in cast")
            return None

        # Extract author info with logging
        author = cast.get('author', {})

        # Extract username and display name
        username = author.get('username', 'unknown')
        display_name = author.get('display_name', username)

        # Extract reactions with logging
        reactions = cast.get('reactions', {})
        likes = reactions.get('likes_count', 0)
        recasts = reactions.get('recasts_count', 0)

        # Extract replies with logging
        replies = cast.get('replies', {})
        reply_count = replies.get('count', 0)

        # Get timestamp
        timestamp = cast.get('timestamp', '')

        # Build formatted string
        formatted_cast = f"""
Post by {display_name} (@{username})
Time: {timestamp}
Engagement: {likes} likes, {recasts} recasts, {reply_count} replies
Text: {text}
"""
        return formatted_cast.strip()

    except Exception as e:
        print(f"Error formatting cast: {str(e)}")
        print(f"Full cast data that caused error: {cast}")
        return None
