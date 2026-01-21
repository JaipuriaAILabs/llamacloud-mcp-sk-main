import click
import os

from mcp.server.fastmcp import Context, FastMCP
from llama_cloud_services import LlamaExtract
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from typing import Awaitable, Callable, Optional


# MCP instance will be created in main() with proper port configuration
mcp = None


def make_index_tool(
    index_name: str,
    project_name: Optional[str],
    org_id: Optional[str],
    api_key: Optional[str] = None
) -> Callable[[Context, str], Awaitable[str]]:
    async def tool(ctx: Context, query: str) -> str:
        try:
            await ctx.info(f"Querying index: {index_name} with query: {query}")
            index = LlamaCloudIndex(
                name=index_name,
                project_name=project_name,
                organization_id=org_id,
                api_key=api_key,
            )
            response = await index.as_retriever().aretrieve(query)
            return str(response)
        except Exception as e:
            await ctx.error(f"Error querying index: {str(e)}")
            return f"Error querying index: {str(e)}"

    return tool


def make_extract_tool(
    agent_name: str,
    project_name: Optional[str],
    org_id: Optional[str],
    api_key: Optional[str] = None
) -> Callable[[Context, str], Awaitable[str]]:
    async def tool(ctx: Context, file_path: str) -> str:
        """Extract data using a LlamaExtract Agent from the given file."""
        try:
            await ctx.info(
                f"Extracting data using agent: {agent_name} with file path: {file_path}"
            )
            llama_extract = LlamaExtract(
                organization_id=org_id,
                project_name=project_name,
                api_key=api_key,
            )
            extract_agent = llama_extract.get_agent(name=agent_name)
            result = await extract_agent.aextract(file_path)
            return str(result)
        except Exception as e:
            await ctx.error(f"Error extracting data: {str(e)}")
            return f"Error extracting data: {str(e)}"

    return tool


@click.command()
@click.option(
    "--index",
    "indexes",
    multiple=True,
    required=False,
    type=str,
    help="Index definition in the format name:description:api_key:org_id:project_name. Can be used multiple times. "
         "Optional: api_key, org_id, and project_name can be omitted to use defaults.",
)
@click.option(
    "--extract-agent",
    "extract_agents",
    multiple=True,
    required=False,
    type=str,
    help="Extract agent definition in the format name:description. Can be used multiple times.",
)
@click.option(
    "--project-name", required=False, type=str, help="Project name for LlamaCloud"
)
@click.option(
    "--org-id", required=False, type=str, help="Organization ID for LlamaCloud"
)
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    help='Transport to run the MCP server on. One of "stdio", "sse", "streamable-http".',
)
@click.option("--api-key", required=False, type=str, help="API key for LlamaCloud")
@click.option("--port", required=False, type=int, help="Port to run the server on (for sse/streamable-http transports)")
def main(
    indexes: Optional[list[str]],
    extract_agents: Optional[list[str]],
    project_name: Optional[str],
    org_id: Optional[str],
    transport: str,
    api_key: Optional[str],
    port: Optional[int],
) -> None:
    global mcp

    api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise click.BadParameter(
            "API key not found. Please provide an API key or set the LLAMA_CLOUD_API_KEY environment variable."
        )
    else:
        os.environ["LLAMA_CLOUD_API_KEY"] = api_key

    # Get port from parameter or environment variable
    if port is None and transport in ["sse", "streamable-http"]:
        port = int(os.getenv("PORT", "8000"))

    # Initialize FastMCP with port and host if needed
    # Render requires binding to 0.0.0.0 to be accessible
    if transport in ["sse", "streamable-http"] and port:
        mcp = FastMCP("llama-index-server", port=port, host="0.0.0.0")
    else:
        mcp = FastMCP("llama-index-server")

    # Parse indexes into (name, description, api_key, org_id, project_name) tuples
    index_info = []
    if indexes:
        for idx in indexes:
            parts = idx.split(":")
            if len(parts) < 2:
                raise click.BadParameter(
                    f"Index '{idx}' must be in the format name:description[:api_key:org_id:project_name]"
                )

            name = parts[0]
            description = parts[1]
            # Optional per-index credentials (fallback to defaults if not provided)
            idx_api_key = parts[2] if len(parts) > 2 else api_key
            idx_org_id = parts[3] if len(parts) > 3 else org_id
            idx_project_name = parts[4] if len(parts) > 4 else project_name

            index_info.append((name, description, idx_api_key, idx_org_id, idx_project_name))

    # Parse extract agents into (name, description, api_key, org_id, project_name) tuples if provided
    extract_agent_info = []
    if extract_agents:
        for agent in extract_agents:
            parts = agent.split(":")
            if len(parts) < 2:
                raise click.BadParameter(
                    f"Extract agent '{agent}' must be in the format name:description[:api_key:org_id:project_name]"
                )

            name = parts[0]
            description = parts[1]
            # Optional per-agent credentials (fallback to defaults if not provided)
            agent_api_key = parts[2] if len(parts) > 2 else api_key
            agent_org_id = parts[3] if len(parts) > 3 else org_id
            agent_project_name = parts[4] if len(parts) > 4 else project_name

            extract_agent_info.append((name, description, agent_api_key, agent_org_id, agent_project_name))

    # Dynamically register a tool for each index
    for name, description, idx_api_key, idx_org_id, idx_project_name in index_info:
        tool_func = make_index_tool(name, idx_project_name, idx_org_id, idx_api_key)
        mcp.tool(name=f"query_{name}", description=description)(tool_func)

    # Dynamically register a tool for each extract agent, if any
    for name, description, agent_api_key, agent_org_id, agent_project_name in extract_agent_info:
        tool_func = make_extract_tool(name, agent_project_name, agent_org_id, agent_api_key)
        mcp.tool(name=f"extract_{name}", description=description)(tool_func)

    # Run the server (port is already configured in FastMCP constructor)
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
