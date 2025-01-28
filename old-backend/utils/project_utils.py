from openai import OpenAI
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import time

def generate_domain_association(domain: str) -> dict:
    """Generate Farcaster domain association data."""
    # Create a new Ethereum account for signing
    account = Account.create()

    # Prepare the message
    message = {
        "domain": domain,
        "timestamp": int(time.time()),
        "expirationTime": int(time.time()) + (90 * 24 * 60 * 60)  # 90 days
    }

    # Sign the message
    encoded_message = encode_defunct(text=json.dumps(message, separators=(',', ':')))
    signature = account.sign_message(encoded_message)

    return {
        "message": message,
        "signature": signature.signature.hex(),
        "signingKey": account.key.hex(),
        "json": {
            "message": message,
            "signature": signature.signature.hex(),
            "signingKey": account.key.hex()
        }
    }
