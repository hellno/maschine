import re
from backend.utils.package_commands import handle_package_install_commands

# Reuse the actual pattern from implementation
PATTERN = r"(?:```.*?[\s\n]*)?(pnpm add|npm install)\s+((?:--\S+\s+)*[^\n`]*)(?:```)?"

test_cases = [
    (
        "```bash npm install js-sha256```",
        [("npm install", "js-sha256")]
    ),
    (
        "pnpm add zustand lodash-es",
        [("pnpm add", "zustand lodash-es")]
    ),
    (
        "Some text before\n```bash pnpm add @types/node --save-dev```\nSome text after",
        [("pnpm add", "@types/node --save-dev")]
    ),
    (
        "npm install --save-dev typescript @types/node",
        [("npm install", "--save-dev typescript @types/node")]
    ),
    (
        "Multiple commands:\n```pnpm add package1```\nnpm install package2",
        [("pnpm add", "package1"), ("npm install", "package2")]
    ),
    (
        "Invalid formats:\npnpmadd nospaces\nnpm install ",
        []
    )
]

def test_package_command_parsing():
    for idx, (input_text, expected) in enumerate(test_cases):
        matches = list(re.finditer(PATTERN, input_text, re.MULTILINE | re.IGNORECASE))
        results = [(m.group(1).lower(), m.group(2).strip()) for m in matches]
        
        assert results == expected, f"""
Test case {idx + 1} failed:
Input: {input_text}
Expected: {expected}
Got: {results}
"""
