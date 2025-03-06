import re
import modal

def handle_package_install_commands(
    aider_result: str,
    sandbox: modal.Sandbox,
    parse_process
) -> None:
    """Parse and execute pnpm/npm install commands from Aider output"""

    # Match both formats:
    # 1. ```bash pnpm add package-name```
    # 2. pnpm add package-name (at the beginning of a line)
    # Supports multiple packages and optional flags

    pattern = r"(?:```.*?[\s\n]*)?(pnpm add|npm install)\s+((?:--\S+\s+)*[^\n`]*)(?:```)?"
    matches = list(re.finditer(pattern, aider_result, re.MULTILINE | re.IGNORECASE))

    print(
        f"[code_service] Found {len(matches)} package install commands in aider output"
    )

    for match in matches:
        command = match.group(1).lower()
        packages = match.group(2).strip()
        if not packages:
            continue

        try:
            print(f"[code_service] Installing packages: {packages}")
            install_proc = sandbox.exec("pnpm", "add", *packages.split())

            # Use the parsing function passed as parameter
            logs, exit_code = parse_process(install_proc)

            if exit_code != 0:
                print(f"[code_service] pnpm add failed with code {exit_code}")
                print("Installation logs:", "\n".join(logs))

        except Exception as e:
            error_msg = f"Error installing packages {packages}: {e}"
            print(f"[code_service] {error_msg}")
