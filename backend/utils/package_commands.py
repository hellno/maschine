import re
import modal
import json
import os
from packaging.version import Version

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

    # Add debug logging to show relevant part of aider output containing commands
    if len(aider_result) > 500:
        print(f"[package_commands] Analyzing aider output (truncated): {aider_result[:500]}...")
    else:
        print(f"[package_commands] Analyzing aider output: {aider_result}")
    
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

def extract_invalid_package_info(error_message: str) -> list[tuple[str, str, str]]:
    """
    Extract all package names, requested versions and available versions from ERR_PNPM_NO_MATCHING_VERSION errors
    
    Returns:
        List of tuples, each containing (package_name, requested_version, latest_available_version)
        Empty list if no matches found
    """
    invalid_packages = []
    
    # Find all package version errors in the log - including scoped packages like @namespace/package
    name_version_matches = re.finditer(r'No matching version found for ((?:@[\w-]+/)?[\w-]+)@\^?([\d.]+)', error_message)
    
    for match in name_version_matches:
        pkg_name, requested_version = match.groups()
        
        # Try to find the latest version for this specific package
        latest_match = re.search(rf'The latest release of {re.escape(pkg_name)} is "([^"]+)"', error_message)
        latest_version = latest_match.group(1) if latest_match else ""
        
        invalid_packages.append((pkg_name, requested_version, latest_version))
    
    return invalid_packages

def fix_invalid_package_versions(repo_dir: str, package_info_list: list[tuple[str, str, str]]) -> list[str]:
    """
    Fix multiple invalid package versions in package.json
    
    Args:
        repo_dir: Repository directory containing package.json
        package_info_list: List of tuples (pkg_name, requested_version, latest_version)
        
    Returns:
        List of package names that were fixed
    """
    package_json_path = os.path.join(repo_dir, "package.json")
    if not os.path.exists(package_json_path):
        return []
    
    fixed_packages = []
    
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        made_changes = False
        
        for pkg_name, requested_version, latest_version in package_info_list:
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in package_data and pkg_name in package_data[dep_type]:
                    old_version = package_data[dep_type][pkg_name]
                    
                    # Use latest version if provided, otherwise use a conservative version
                    if latest_version:
                        try:
                            # Only use latest version if it's newer than requested version
                            if not requested_version or Version(latest_version) >= Version(requested_version):
                                package_data[dep_type][pkg_name] = f"^{latest_version}"
                                print(f"[package_commands] Using latest version {latest_version} for {pkg_name}")
                            else:
                                print(f"[package_commands] Warning: Latest version {latest_version} is older than requested {requested_version} for {pkg_name}")
                                package_data[dep_type][pkg_name] = f"^{requested_version}"
                        except ValueError:
                            # If version parsing fails, use the latest version anyway
                            package_data[dep_type][pkg_name] = f"^{latest_version}"
                            print(f"[package_commands] Using latest version {latest_version} for {pkg_name} (couldn't compare versions)")
                    else:
                        package_data[dep_type][pkg_name] = "^0.1.0"
                    
                    print(f"[package_commands] Fixed {pkg_name} version from {old_version} to {package_data[dep_type][pkg_name]}")
                    fixed_packages.append(pkg_name)
                    made_changes = True
        
        if made_changes:
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
    
    except Exception as e:
        print(f"[package_commands] Error fixing package versions: {str(e)}")
    
    return fixed_packages

def fix_invalid_package_version(repo_dir: str, pkg_name: str, latest_version: str = "") -> bool:
    """
    Fix a single invalid package version in package.json
    
    Args:
        repo_dir: Repository directory containing package.json
        pkg_name: Name of the package to fix
        latest_version: Latest available version (optional)
        
    Returns:
        True if fixed, False otherwise
    """
    fixed_packages = fix_invalid_package_versions(repo_dir, [(pkg_name, "", latest_version)])
    return len(fixed_packages) > 0
