#!/usr/bin/env python3
"""
Startup script for deploying LlamaCloud MCP server on Render.
This script reads configuration from environment variables and starts the MCP server.
"""
import os
import sys
from llamacloud_mcp.main import main

def start():
    """Start the MCP server with configuration from environment variables."""

    # Get global/default configuration from environment variables
    default_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    default_org_id = os.getenv("ORG_ID")
    default_project_name = os.getenv("PROJECT_NAME")
    transport = os.getenv("TRANSPORT", "streamable-http")
    port = os.getenv("PORT", "8000")  # Render provides PORT env var

    # Legacy single index support (for backward compatibility)
    legacy_index_name = os.getenv("INDEX_NAME", "")
    legacy_index_description = os.getenv("INDEX_DESCRIPTION", "Search index")

    # Build the command line arguments
    args = []

    # Collect all indexes from numbered environment variables (INDEX_1, INDEX_2, etc.)
    indexes = []
    index_num = 1
    while True:
        index_config = os.getenv(f"INDEX_{index_num}")
        if not index_config:
            break
        indexes.append(index_config)
        index_num += 1

    # Add legacy index if no numbered indexes found
    if not indexes and legacy_index_name:
        # Build legacy format with defaults
        legacy_parts = [legacy_index_name, legacy_index_description]
        if default_api_key:
            legacy_parts.append(default_api_key)
        if default_org_id:
            legacy_parts.append(default_org_id)
        if default_project_name:
            legacy_parts.append(default_project_name)
        indexes.append(":".join(legacy_parts))

    # Validate that we have at least one index
    if not indexes:
        print("ERROR: No indexes configured. Set INDEX_1, INDEX_2, etc. or INDEX_NAME", file=sys.stderr)
        sys.exit(1)

    # Add all indexes
    for index_config in indexes:
        args.extend(["--index", index_config])

    # Add default project name if configured (used as fallback)
    if default_project_name:
        args.extend(["--project-id", default_project_name])

    # Add default org ID (used as fallback)
    if default_org_id:
        args.extend(["--org-id", default_org_id])

    # Add transport
    args.extend(["--transport", transport])

    # Add default API key (used as fallback)
    if default_api_key:
        args.extend(["--api-key", default_api_key])

    print(f"Starting LlamaCloud MCP Server on port {port}...")
    print(f"Transport: {transport}")
    print(f"Configured {len(indexes)} index(es)")
    for i, idx in enumerate(indexes, 1):
        # Only print first 2 fields to avoid exposing API keys
        parts = idx.split(":")
        print(f"  Index {i}: {parts[0]} - {parts[1] if len(parts) > 1 else 'No description'}")

    # Set sys.argv to simulate command line arguments
    sys.argv = ["llamacloud-mcp"] + args

    # Run the main function
    try:
        main()
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    start()
