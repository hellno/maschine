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


class NeynarPostTool:
    name: str = "neynar_post_tool"
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

    def reply_to_cast(self, text: str, parent_hash: str, parent_fid: int) -> str:
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
        return self._run(text, parent_cast_id=parent_cast_id)

    def validate_text(self, text: str) -> bool:
        # maximum byte length is 320 bytes
        if len(text.encode("utf-8")) > 320:
            raise ValueError("Post content is too long. Maximum 320 bytes allowed.")
        return True

    def _get_credentials(self) -> str:
        """
        Get API key from environment variables
        Returns:
            str: api_key
        """
        api_key = os.getenv("NEYNAR_API_KEY")
        if not api_key:
            raise ValueError("NEYNAR_API_KEY environment variable not set")
        return api_key

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
        api_key = self._get_credentials()
        url = "https://hub-api.neynar.com/v1/submitMessage"

        headers = {
            "accept": "application/json",
            "api_key": api_key,
            "content-type": "application/octet-stream",
        }

        try:
            # Get required Farcaster credentials
            app_signer = os.getenv("FARCASTER_APP_SIGNER")
            user_fid = os.getenv("FARCASTER_ID")
            if not app_signer or not user_fid:
                raise ValueError(
                    "FARCASTER_APP_SIGNER and FARCASTER_ID environment variables must be set"
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
