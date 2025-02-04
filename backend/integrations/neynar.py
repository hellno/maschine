import os
from typing import Dict, Optional, List
import requests
import unicodedata
from farcaster.fcproto.message_pb2 import (
    SignatureScheme,
    HashScheme,
    Embed,
    MessageType,
    FarcasterNetwork,
    MessageData,
    CastAddBody,
)
from farcaster import Message
import time

FARCASTER_EPOCH = 1609459200  # January 1, 2021 UTC


class NeynarError(Exception):
    """Base exception class for Neynar API errors"""

    pass


def _get_api_key() -> str:
    api_key = os.getenv("NEYNAR_API_KEY")
    if not api_key:
        raise ValueError("NEYNAR_API_KEY environment variable not set")
    return api_key


def get_author_display(author: Dict) -> str:
    """Extract author display name and username safely"""
    display_name = author.get("display_name", "Anonymous")
    username = author.get("username", "unknown")
    return f"{display_name} (@{username})"


def get_location_string(author: Dict) -> str:
    """Safely extract and format location information"""
    try:
        profile = author.get("profile", {})
        location = profile.get("location", {}).get("address", {})
        city = location.get("city")
        country = location.get("country")

        if city and country:
            return f" from {city}, {country}"
    except Exception:
        pass
    return ""


def get_channel_string(cast_data: Dict) -> str:
    """Safely extract and format channel information"""
    try:
        channel = cast_data.get("channel", {}).get("name")
        return f" in #{channel}" if channel else ""
    except Exception:
        return ""


def get_follower_string(author: Dict) -> str:
    """Safely extract and format follower count"""
    try:
        follower_count = author.get("follower_count", 0)
        return f" (has {follower_count:,} followers)"
    except Exception:
        return ""


def format_cast(
    cast: dict, include_location: bool = True, include_stats: bool = True
) -> Optional[str]:
    """
    Format a single cast into a readable string
    Args:
        cast: Dictionary containing cast data from Neynar API or Dagster output
    Returns:
        Optional[str]: Formatted cast string or None if formatting fails
    """
    try:
        print("format_cast: cast %s", cast)
        text = cast.get("text")
        if not text:
            return None

        author = cast.get("author", {})
        reactions = cast.get("reactions", {})
        replies = cast.get("replies", {})

        # Format engagement metrics
        likes = reactions.get("likes_count", 0)
        recasts = reactions.get("recasts_count", 0)
        reply_count = replies.get("count", 0)

        # Get timestamp
        timestamp = cast.get("timestamp", "")

        # Build formatted string using helper functions
        formatted_cast = f"""
        posted by {get_author_display(author)}
        {get_location_string(author) if include_location else ""}
        {get_channel_string(cast)}
        {get_follower_string(author) if include_stats else ""}
        Date: {timestamp}
        {f"Engagement: {likes} likes {recasts} recasts {reply_count} replies" if include_stats else ""}
        Text: {text}
        """
        return formatted_cast
    except Exception as e:
        print("format_cast error: %s", e)
        return None


class NeynarPost:
    description: str = "Posts content to Farcaster social media network. Input should be the text content to post."

    def _run(self, text: str, **kwargs) -> str:
        """
        Execute the posting tool
        Args:
            text: The content to post (either string or dict with 'text' key)
            **kwargs: Additional arguments including optional embed for quote-tweets
        Returns:
            str: Response summary of the posting operation
        """
        try:
            print(f"NeynarPostToo._run: text {text}, kwargs {kwargs}")
            if not text.strip():
                raise ValueError("Post content cannot be empty")

            # Normalize Unicode characters and emojis
            text = unicodedata.normalize("NFKC", text)
            # Handle Unicode escape sequences
            text = text.encode("utf-16", "surrogatepass").decode("utf-16")

            if self.validate_text(text):
                embeds = kwargs.get("embeds", [])
                parent_cast_id = kwargs.get("parent_cast_id", [])
                return self._post_content(
                    text, embeds=embeds, parent_cast_id=parent_cast_id
                )
        except Exception as e:
            return f"Error processing post content: {str(e)}"

    def quote_cast(self, text: str, cast_hash: str, cast_fid: int) -> str:
        """
        Create a quote-tweet of another cast
        Args:
            text: The content to post
            cast_hash: Hash of the cast to quote
            cast_fid: FID of the cast author to quote
        Returns:
            str: Response summary of the posting operation
        """
        embeds = [{"cast_id": {"hash": cast_hash, "fid": cast_fid}}]
        return self._run(text, embeds=embeds)

    def reply_to_cast(
        self,
        text: str,
        parent_hash: str,
        parent_fid: int,
        embeds: Optional[List[Dict]] = [],
    ) -> str:
        """
        Reply to an existing cast
        Args:
            text: The content to post
            parent_hash: Hash of the parent cast to reply to
            parent_fid: FID of the parent cast author
        Returns:
            str: Response summary of the posting operation
        """
        parent_cast_id = {"hash": parent_hash, "fid": parent_fid}
        return self._run(text, parent_cast_id=parent_cast_id, embeds=embeds)

    def validate_text(self, text: str) -> bool:
        # maximum byte length is 320 bytes
        if len(text.encode("utf-8")) > 320:
            raise ValueError("Post content is too long. Maximum 320 bytes allowed.")
        return True

    def _post_content(
        self,
        text: str,
        embeds: Optional[List[Dict]] = [],
        parent_cast_id: Optional[Dict] = {},
    ) -> str:
        """
        Post content to Farcaster using Neynar API
        Args:
            text: The content to post
            embed: Optional embed data for quote-tweets
            parent_cast_id: Optional parent cast ID for replies
        Returns:
            str: Summary of the posting operation
        """
        print("NeynarPostTool _post_content text: %s", text)
        print("NeynarPostTool _post_content embeds: %s", embeds)
        print("NeynarPostTool _post_content parent_cast_id: %s", parent_cast_id)
        api_key = _get_api_key()
        url = "https://hub-api.neynar.com/v1/submitMessage"

        headers = {
            "accept": "application/json",
            "api_key": api_key,
            "content-type": "application/octet-stream",
        }

        try:
            # Get required Farcaster credentials
            app_signer = os.getenv("FARCASTER_APP_SIGNER")
            user_fid = os.getenv("FID")
            print(f"using fid {user_fid} and app_signer {app_signer[:10]}")
            if not app_signer or not user_fid:
                raise ValueError(
                    "FARCASTER_APP_SIGNER and FID environment variables must be set"
                )

            # Build and sign the message
            message_builder = Message.MessageBuilder(
                HashScheme.HASH_SCHEME_BLAKE3,
                SignatureScheme.SIGNATURE_SCHEME_ED25519,
                bytes.fromhex(app_signer[2:]),  # Remove '0x' prefix from hex string
            )

            # Process parent_cast_id to ensure hash is in bytes format
            processed_parent = None
            if parent_cast_id:
                processed_parent = parent_cast_id.copy()
                if "hash" in processed_parent:
                    # Convert hash string to bytes
                    if isinstance(processed_parent["hash"], str):
                        processed_parent["hash"] = bytes.fromhex(
                            processed_parent["hash"][2:]
                            if processed_parent["hash"].startswith("0x")
                            else processed_parent["hash"]
                        )

            # Process embeds to ensure hash is in bytes format
            processed_embeds = []
            if embeds:
                for embed in embeds:
                    if "cast_id" in embed:
                        cast_id = embed["cast_id"]
                        # Convert hash string to bytes
                        if isinstance(cast_id["hash"], str):
                            cast_id["hash"] = bytes.fromhex(
                                cast_id["hash"][2:]
                                if cast_id["hash"].startswith("0x")
                                else cast_id["hash"]
                            )
                        processed_embeds.append(Embed(**embed))
                    elif "url" in embed:
                        processed_embeds.append(Embed(url=embed["url"]))

            data = None
            # Set parent cast ID fields directly if it exists
            if processed_parent:
                data = MessageData(
                    type=MessageType.MESSAGE_TYPE_CAST_ADD,
                    fid=int(user_fid),
                    timestamp=int(time.time()) - FARCASTER_EPOCH,
                    network=FarcasterNetwork.FARCASTER_NETWORK_MAINNET,
                    cast_add_body=CastAddBody(
                        text=text,
                        embeds=[],
                        mentions=[],
                        mentions_positions=[],
                        parent_cast_id=processed_parent,
                    ),
                )
                if embeds:
                    data.cast_add_body.embeds.extend(processed_embeds)
            else:
                data = message_builder.cast.add(
                    fid=int(user_fid),
                    text=text,
                    embeds=processed_embeds,
                )
            msg = message_builder.message(data)
            print(f"message: {msg}")
            # Submit the message
            response = requests.post(url, data=msg.SerializeToString(), headers=headers)
            print("response from neynar: %s", response)

            result = response.json()
            print("result: %s", result)

            if response.status_code != 200:
                print("Error posting content %s", response.text)
                return f"Error posting content: {response.text}"
            # Format success response
            data = result.get("data", {})
            type = data.get("type")
            hash = result.get("hash")
            response = ""
            if type and hash:
                response = f"Successfully posted content! Hash: {hash}"
            else:
                response = f"Post created but no cast details returned: {result}"
            print("neynar response: %s", response)
            return response
        except Exception as e:
            error_msg = f"Error posting content: {str(e)}"
            print(f"NeynarPostTool info error: {error_msg}")
            print(f"NeynarPostTool error: {error_msg}")
            if hasattr(e.response, "json"):
                try:
                    error_details = e.response.json()
                    error_msg += (
                        f"\nAPI Error: {error_details.get('message', 'Unknown error')}"
                    )
                except Exception:
                    pass
            raise NeynarError(f"NeynarPostTool error: {error_msg}")


def get_conversation_from_cast(cast_hash: str, reply_depth: int = 1) -> str:
    """
    Get the conversation thread for a specific cast
    Args:
        cast_hash: Hash of the cast to get conversation for
        reply_depth: How many levels of replies to include (default 1)
    Returns:
        str: Conversation of formatted casts including the cast, its parents and its replies
    """
    try:
        print(f"NeynarFeedTool get_conversation for cast_hash {cast_hash}")
        api_key = _get_api_key()
        fid = os.getenv("FID")
        if not fid:
            raise ValueError("FID environment variable not set")

        headers = {"accept": "application/json", "api_key": api_key}

        url = "https://api.neynar.com/v2/farcaster/cast/conversation"
        params = {
            "identifier": cast_hash,
            "type": "hash",
            "reply_depth": reply_depth,
            "include_chronological_parent_casts": "true",
            "viewer_fid": fid,
            "fold": "above",
            "limit": 20,
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        conversation = response.json().get("conversation")
        print(f"Retrieved conversation for cast {cast_hash}: {conversation}")
        main_cast = conversation.get("cast")
        parent_casts = conversation.get("chronological_parent_casts", [])
        child_casts = main_cast.get("direct_replies", [])
        casts = parent_casts + [main_cast] + child_casts
        return "\n".join([format_cast(c, include_stats=False) for c in casts if c])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching conversation: {str(e)}")
        raise NeynarError(f"Failed to fetch conversation: {str(e)}")
