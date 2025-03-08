import re
import modal
import json
import os

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
        error_msg = f"Process handling failed. exit code: {exit_code} error: {str(e)}"
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
            print(f"[code_service] Installing packages {len(packages.split())}: {packages}")
            install_proc = sandbox.exec("pnpm", "add", *packages.split())

            # Use the parsing function passed as parameter
            logs, exit_code = parse_process(install_proc)

            if exit_code != 0:
                print(f"pnpm add failed with code {exit_code}")
                print("Installation logs:", "\n".join(logs))

        except Exception as e:
            error_msg = f"Error installing packages {packages}: {e}"
            print(f"[code_service] {error_msg}")

def extract_invalid_package_info(error_message: str) -> tuple[str, str, str]:
    """
    Extract package name, requested version and available version from an ERR_PNPM_NO_MATCHING_VERSION error
    
    Returns:
        Tuple of (package_name, requested_version, latest_available_version)
        If parsing fails, returns empty strings
    """
    # Match pattern for: No matching version found for package@^x.y.z
    name_version_match = re.search(r'No matching version found for ([^\s@]+)@\^?(\d+\.\d+\.\d+)', error_message)
    
    # Match pattern for: The latest release of package is "x.y.z"
    latest_match = re.search(r'The latest release of [^\s]+ is "([^"]+)"', error_message)
    
    if name_version_match:
        pkg_name, requested_version = name_version_match.groups()
        latest_version = latest_match.group(1) if latest_match else ""
        return pkg_name, requested_version, latest_version
    
    return "", "", ""

def fix_invalid_package_version(repo_dir: str, pkg_name: str, latest_version: str = "") -> bool:
    """
    Fix an invalid package version in package.json
    
    Args:
        repo_dir: Repository directory containing package.json
        pkg_name: Name of the package to fix
        latest_version: Latest available version (optional)
        
    Returns:
        True if fixed, False otherwise
    """
    package_json_path = os.path.join(repo_dir, "package.json")
    if not os.path.exists(package_json_path):
        return False
    
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        fixed = False
        for dep_type in ['dependencies', 'devDependencies']:
            if dep_type in package_data and pkg_name in package_data[dep_type]:
                old_version = package_data[dep_type][pkg_name]
                
                # Use latest version if provided, otherwise use a conservative version
                if latest_version:
                    package_data[dep_type][pkg_name] = f"^{latest_version}"
                else:
                    package_data[dep_type][pkg_name] = "^0.1.0"
                
                print(f"[package_commands] Fixed {pkg_name} version from {old_version} to {package_data[dep_type][pkg_name]}")
                fixed = True
        
        if fixed:
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            return True
    
    except Exception as e:
        print(f"[package_commands] Error fixing package version: {str(e)}")
    
    return False
