import re
import modal

def parse_sandbox_process(process, prefix="") -> tuple[list, int]:
    """Safely parse stdout/stderr from a sandbox process using Modal's StreamReader."""
    logs = []
    exit_code = -1

    try:
        # Handle stdout - check if bytes need decoding
        for line in process.stdout:
            try:
                if isinstance(line, bytes):  # Handle both str and bytes
                    decoded = line.decode("utf-8", "ignore").strip()
                else:
                    decoded = str(line).strip()  # Convert to string if needed
                logs.append(decoded)
                # print(f"[{prefix}] {decoded}")
            except UnicodeDecodeError as ude:
                error_msg = f"Decode error: {str(ude)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")

        # Handle stderr the same way
        for line in process.stderr:
            try:
                if isinstance(line, bytes):
                    decoded = line.decode("utf-8", "ignore").strip()
                else:
                    decoded = str(line).strip()
                logs.append(decoded)
                # print(f"[{prefix} ERR] {decoded}")
            except UnicodeDecodeError as ude:
                error_msg = f"Decode error: {str(ude)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")

        # Get exit code after reading all output
        exit_code = process.wait()

    except Exception as e:
        error_msg = f"Process handling failed: {str(e)}"
        logs.append(error_msg)
        print(f"[{prefix} CRITICAL] {error_msg}")

    return logs, exit_code

def handle_package_install_commands(
    aider_result: str,
    sandbox: modal.Sandbox,
    parse_process
) -> None:
    """Parse and execute pnpm/npm install commands from Aider output"""

    # ai! create a separate test file that runs through these
    # Match both formats:
    # 1. ```bash npm install package-name```
    # 2. pnpm add package-name (at the beginning of a line)
    # 3. pnpm add p1 p2 p3
    # Supports multiple packages and optional flags

    pattern = r"(?:```.*?[\s\n]*)?(pnpm add|npm install)\s+((?:--\S+\s+)*[^\n`]*)(?:```)?"
    matches = list(re.finditer(pattern, aider_result, re.MULTILINE | re.IGNORECASE))

    print(
        f"[code_service] Found {len(matches)} package install commands in aider output"
    )

    for match in matches:
        # command = match.group(1).lower()
        packages = match.group(2).strip()
        if not packages:
            continue

        try:
            print(f"[code_service] Installing packages: {packages}")
            install_proc = sandbox.exec("pnpm", "add", *packages.split())

            # Use the parsing function passed as parameter
            logs, exit_code = parse_process(install_proc)

            if exit_code != 0:
                print(f"pnpm add failed with code {exit_code}")
                print("Installation logs:", "\n".join(logs))

        except Exception as e:
            error_msg = f"Error installing packages {packages}: {e}"
            print(f"[code_service] {error_msg}")
