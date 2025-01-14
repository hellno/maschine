import requests
from typing import List, Dict, Optional

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
    url = f"https://api.neynar.com/v2/farcaster/feed?feed_type=filter&filter_type=fids&fids={fid}&with_recasts=false&limit={nr_casts}"

    headers = {
        "accept": "application/json",
        "x-api-key": process.env.NEYNAR_API_KEY
    }

    response = requests.get(url, headers=headers)
    print(f'get_user_casts response', response.text)
    return response.json().casts

def format_cast(cast: dict) -> Optional[str]:
    """
    Format a single cast into a readable string
    Args:
        cast: Dictionary containing cast data from Neynar API or Dagster output
    Returns:
        Optional[str]: Formatted cast string or None if formatting fails
    """
    try:
        logger.info('format_cast: cast %s', cast)
        text = cast.get('text')
        if not text:
            return None

        author = cast.get('author', {})
        reactions = cast.get('reactions', {})
        replies = cast.get('replies', {})

        # Format engagement metrics
        likes = reactions.get('likes_count', 0)
        recasts = reactions.get('recasts_count', 0)
        reply_count = replies.get('count', 0)

        # Get timestamp
        timestamp = cast.get('timestamp', '')

        # Build formatted string using helper functions
        formatted_cast = f"""
        Post from {get_author_display(author)}
        {get_channel_string(cast)}
        Date: {timestamp}
        Engagement:
        {likes} likes {recasts} recasts {reply_count} replies
        Text: {text}
        """
        return formatted_cast
    except Exception as e:
        logger.error('format_cast error: %s', e)
        return None
