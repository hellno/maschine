from openai import OpenAI
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import time
import re

def generate_project_name(prompt: str, deepseek: OpenAI) -> str:
    """Generate a project name from the user's prompt using LLM."""
    try:
        response = deepseek.chat.completions.create(
            model="deepseek-coder",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant that generates short, memorable project names for a Farcaster Frame project. Only respond with the project name, 2-3 words max, no 'or' or &*/ chars."
            }, {
                "role": "user",
                "content": f"Generate a short, memorable project name based on this description: {prompt}"
            }],
            max_tokens=50,
            temperature=2,
        )
        project_name = response.choices[0].message.content.strip().replace('"', '')
        return project_name[:50]  # Limit length
    except Exception as e:
        print(f"Warning: Could not generate project name: {str(e)}")
        return "new-frame-project"

def get_template_customization_prompt(project_name: str, user_prompt: str) -> str:
    """Generate the initial setup prompt for the project."""
    return f"""Create a Farcaster Frame called "{project_name}" based on this description:
{user_prompt}

Focus on:
1. Updating the Frame component in src/components/Frame.tsx
2. Adding any needed constants to src/lib/constants.ts
3. Keeping the implementation simple and focused
4. Using best practices for Frames

The frame should be engaging and interactive while following Farcaster Frame best practices."""

def get_metadata_prompt(project_name: str) -> str:
    """Generate metadata update prompt."""
    return f"""
Update the following files to customize the project metadata:
1. In src/lib/constants.ts:
   set PROJECT_ID to "{project_name}"
   set PROJECT_TITLE to "{project_name}"
   set PROJECT_DESCRIPTION to a brief description of the project
2. In src/app/opengraph-image.tsx:
   - Reflect the project name "{project_name}"
   - Include a matching color or layout
   - Keep a simple one-page brand layout
"""

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

def sanitize_project_name(name: str) -> str:
    """Sanitize project name for use in URLs and file systems."""
    # get only the first line
    name = name.split("\n")[0]

    # Convert to lowercase
    sanitized = name.lower()
    
    # Replace invalid chars with dash
    sanitized = re.sub(r"[^a-z0-9._-]", "-", sanitized)
    
    # Replace multiple dashes with single dash
    sanitized = re.sub(r"-+", "-", sanitized)
    
    # Remove leading/trailing dashes
    sanitized = sanitized.strip("-")
    
    # Ensure no triple dashes (Vercel requirement)
    sanitized = sanitized.replace("---", "-")
    
    # Truncate to 100 chars
    sanitized = sanitized[:100]
    
    # Return default if empty
    return sanitized or "new-frame-project"
