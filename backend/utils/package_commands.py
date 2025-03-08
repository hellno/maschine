import re
import modal

def parse_sandbox_process(process, prefix="") -> tuple[list, int]:
    """Safely parse stdout/stderr from a sandbox process using Modal's StreamReader."""
    logs = []
    exit_code = -1

    try:
        # Handle stdout with more robust error handling
        for line in process.stdout:
            try:
                if isinstance(line, bytes):
                    # Use 'replace' instead of 'ignore' to handle bad bytes
                    decoded = line.decode("utf-8", "replace").strip()
                else:
                    decoded = str(line).strip()
                logs.append(decoded)
                print(f"[{prefix}] {decoded}")
            except UnicodeDecodeError as ude:
                error_msg = f"Decode error: {str(ude)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")
            except Exception as e:
                error_msg = f"Unexpected error processing stdout: {str(e)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")

        # Handle stderr with more robust error handling
        for line in process.stderr:
            try:
                if isinstance(line, bytes):
                    # Use 'replace' instead of 'ignore' to handle bad bytes
                    decoded = line.decode("utf-8", "replace").strip()
                else:
                    decoded = str(line).strip()
                logs.append(decoded)
                print(f"[{prefix} ERR] {decoded}")
            except UnicodeDecodeError as ude:
                error_msg = f"Decode error: {str(ude)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")
            except Exception as e:
                error_msg = f"Unexpected error processing stderr: {str(e)}"
                logs.append(error_msg)
                print(f"[{prefix} ERR] {error_msg}")

        # Get exit code after reading all output
        try:
            exit_code = process.wait()
        except Exception as e:
            error_msg = f"Error getting exit code: {str(e)}"
            logs.append(error_msg)
            print(f"[{prefix} ERR] {error_msg}")

    except Exception as e:
        error_msg = f"Process handling failed: {str(e)}"
        logs.append(error_msg)
        print(f"[{prefix} CRITICAL] {error_msg}")

    if not logs:
        # Add a placeholder if logs are empty to prevent further issues
        logs = ["No output captured from process"]

    return logs, exit_code

def handle_package_install_commands(
    aider_result: str,
    sandbox: modal.Sandbox,
    parse_process
) -> None:
    """Parse and execute pnpm/npm install commands from Aider output"""

    # Add safety check for sandbox
    if sandbox is None:
        print("[code_service] Error: Cannot install packages - sandbox is None")
        return

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
            print(f"[code_service] Installing packages {len(packages)}: {packages}")
            install_proc = sandbox.exec("pnpm", "add", *packages.split())

            # Use the parsing function passed as parameter
            logs, exit_code = parse_process(install_proc)

            if exit_code != 0:
                print(f"pnpm add failed with code {exit_code}")
                print("Installation logs:", "\n".join(logs))

        except Exception as e:
            error_msg = f"Error installing packages {packages}: {e}"
            print(f"[code_service] {error_msg}")
