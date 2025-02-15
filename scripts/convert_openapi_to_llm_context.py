import os
from tqdm import tqdm
import yaml
from pathlib import Path
from typing import List, Optional, Dict

OUTPUT_PATH = "backend/llm_context/docs"  # Path to write the generated context files


def resolve_schema(schema: Dict, spec: Dict) -> Dict:
    """Resolve $ref references to actual schema components recursively"""
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")[-1]
        resolved = spec["components"]["schemas"].get(ref_path, schema)
        return resolve_schema(resolved, spec)  # Recurse on resolved schema
    
    # Handle nested object properties
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            schema["properties"][prop_name] = resolve_schema(prop_schema, spec)
    
    # Handle array items
    if "items" in schema:
        schema["items"] = resolve_schema(schema["items"], spec)
    
    # Handle anyOf/allOf/oneOf
    for union_type in ["anyOf", "allOf", "oneOf"]:
        if union_type in schema:
            schema[union_type] = [resolve_schema(s, spec) for s in schema[union_type]]
    
    return schema


def convert_openapi_to_llm_context(
    openapi_file: str, api_name: str, additional_skip_words: Optional[List[str]] = None
) -> None:
    """Convert OpenAPI spec to LLM context documentation.

    Args:
        openapi_file: Path to OpenAPI spec file (YAML)
        api_name: Name of API for grouping context files
        additional_skip_words: Optional list of additional words to skip

    Example:
        convert_openapi_to_llm_context('neynar_openapi.yaml', 'neynar', ['temp','demo'])
        # Creates files in backend/llm_context/docs/neynar/ skipping endpoints with temp/demo
    """
    skip_filter = [
        "test",
        "example",
        "mock",
        "sample",
    ]  # Words that indicate test endpoints

    if additional_skip_words:
        skip_filter += additional_skip_words

    try:
        with open(openapi_file, "r") as f:
            spec = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: OpenAPI file not found at {openapi_file}")
        return

    output_dir = Path(OUTPUT_PATH) / api_name
    output_dir.mkdir(parents=True, exist_ok=True)

    items = spec.get("paths", {}).items()
    for path, methods in tqdm(items, desc="Generating context files"):
        for method, details in methods.items():
            if "operationId" not in details:
                continue

            # Skip test/example endpoints
            op_id = details["operationId"].lower()
            description = details.get("description", "").lower()
            if any(
                skip_word in op_id or skip_word in description
                for skip_word in skip_filter
            ):
                continue

            # Generate context content
            content = f"# {details['operationId']}\n\n"
            content += f"**Endpoint**: `{method.upper()} {path}`\n\n"

            if "description" in details:
                content += f"## Description\n{details['description']}\n\n"

            if "parameters" in details:
                content += "## Parameters\n"
                for param in details["parameters"]:
                    # Skip parameters that are references without inline names
                    if "name" not in param:
                        continue
                    content += f"- `{param['name']}` ({param.get('in', 'query')}): {param.get('description', 'No description')}\n"
                content += "\n"

            if "responses" in details:
                content += "## Response\n"
                success_response = details["responses"].get("200", {})
                if "content" in success_response:
                    schema = success_response["content"]["application/json"]["schema"]
                    resolved_schema = resolve_schema(schema, spec)
                    content += "```yaml\n"
                    content += yaml.dump(resolved_schema, sort_keys=False)
                    content += "```\n"

            # Write context file
            filename = f"{api_name}_{details['operationId']}.md"
            output_path = output_dir / filename

            try:
                with open(output_path, "w") as f:
                    f.write(content)
                # print(f"Created context file: {output_path}")
            except IOError as e:
                print(f"Error writing file {output_path}: {str(e)}")


def main():
    openapi_file = "notebooks/specs/Neynar_OAS_v2_spec.yaml"
    api_name = "neynar"
    additional_skip_words = ["temp", "demo", "signer", "delete", "webhook"]
    convert_openapi_to_llm_context(openapi_file, api_name, additional_skip_words)


if __name__ == "__main__":
    main()
