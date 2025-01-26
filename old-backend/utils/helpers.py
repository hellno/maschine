import base64
import os
import re
from typing import Tuple


def generate_random_secret() -> str:
    """Generate a cryptographically secure random secret"""
    return base64.b64encode(os.urandom(32)).decode("utf-8")

def parse_github_url(url: str) -> Tuple[str, str]:
    """Extract (org, repo) from any GitHub URL format"""
    patterns = [
        r"github\.com[:/](?P<org>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?",
        r"^(?P<org>[^/]+)/(?P<repo>[^/]+)$"  # Handle already parsed formats
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group("org"), match.group("repo")
    
    raise ValueError(f"Invalid GitHub URL format: {url}")

def sanitize_project_name(name: str) -> str:
    """Sanitize project name for use in URLs and file systems"""
    name = name.split("\n")[0].lower()
    sanitized = re.sub(r"[^a-z0-9._-]", "-", name)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized.replace("---", "-")[:100]
