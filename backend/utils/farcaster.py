import os
from typing import Dict
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import time
import base64
import re


def generate_domain_association(domain: str) -> dict:
    """Generate a domain association signature for Farcaster frames.

    Args:
        domain: The domain to generate association for (without http/https)

    Returns:
        Dict containing compact and JSON formats of the signed domain association

    Raises:
        ValueError: If domain is invalid or starts with http/https
    """

    try:
        # Validate domain format
        domain = domain.strip().replace("https://", "")

        # Basic domain format validation
        domain_pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        if not re.match(domain_pattern, domain):
            raise ValueError("Invalid domain format")

        # Get environment variables
        fid = int(os.environ.get("FID", 0))
        custody_address = os.environ.get("CUSTODY_ADDRESS", "")
        private_key = os.environ.get("PRIVATE_KEY", "")

        # Validate configuration
        if not all([fid, custody_address, private_key]):
            raise ValueError("Server configuration incomplete")

        # Create header and payload
        header = {"fid": fid, "type": "custody", "key": custody_address}
        payload = {"domain": domain}

        # Encode components to base64url
        def to_base64url(data: dict) -> str:
            json_str = json.dumps(data)
            bytes_data = json_str.encode("utf-8")
            base64_str = base64.urlsafe_b64encode(bytes_data).decode("utf-8")
            return base64_str.rstrip("=")  # Remove padding

        encoded_header = to_base64url(header)
        encoded_payload = to_base64url(payload)

        # Create message to sign
        message = f"{encoded_header}.{encoded_payload}"

        # Create signable message using encode_defunct
        signable_message = encode_defunct(text=message)

        # Sign message using ethereum account
        signed_message = Account.sign_message(signable_message, private_key)

        # Get the signature bytes and encode to base64url
        encoded_signature = (
            base64.urlsafe_b64encode(signed_message.signature)
            .decode("utf-8")
            .rstrip("=")
        )

        return {
            "header": encoded_header,
            "payload": encoded_payload,
            "signature": encoded_signature,
        }

    except Exception as e:
        raise Exception(f"Failed to generate domain association: {str(e)}")
