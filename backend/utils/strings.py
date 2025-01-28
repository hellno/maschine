
import re


def sanitize_project_name(name: str) -> str:
    """Sanitize project name for use in URLs and file systems"""
    name = name.split("\n")[0].lower()
    sanitized = re.sub(r"[^a-z0-9._-]", "-", name)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return sanitized.replace("---", "-")[:100]
