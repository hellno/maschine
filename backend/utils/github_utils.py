import re

def parse_github_url(url: str) -> tuple[str, str]:
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
