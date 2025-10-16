#!/usr/bin/env python
import os
from typing import Literal
from mcp_polygon import server


def transport() -> Literal["stdio", "sse", "streamable-http"]:
    """
    Determine the transport type for the MCP server.
    Defaults to 'stdio' if not set in environment variables.
    """
    mcp_transport_str = os.environ.get("MCP_TRANSPORT", "stdio")

    # These are currently the only supported transports
    supported_transports: dict[str, Literal["stdio", "sse", "streamable-http"]] = {
        "stdio": "stdio",
        "sse": "sse",
        "streamable-http": "streamable-http",
    }

    return supported_transports.get(mcp_transport_str, "stdio")


def configure_http_transport() -> None:
    """
    Configure FastMCP HTTP transport using environment variables.
    Only sets defaults if transport is HTTP-based and variables not already set.

    This function enables Docker container accessibility by setting FASTMCP_HOST
    to 0.0.0.0, which allows the container to accept connections from the host.
    """
    selected_transport = transport()

    # Only configure for HTTP-based transports
    if selected_transport in ("sse", "streamable-http"):
        # Set host to 0.0.0.0 for Docker container accessibility
        # (FastMCP default is 127.0.0.1 which only allows internal container access)
        if "FASTMCP_HOST" not in os.environ:
            os.environ["FASTMCP_HOST"] = "0.0.0.0"

        # Set default port to 8000 (FastMCP default, but explicit is better)
        if "FASTMCP_PORT" not in os.environ:
            os.environ["FASTMCP_PORT"] = "8000"


# Ensure the server process doesn't exit immediately when run as an MCP server
def start_server():
    polygon_api_key = os.environ.get("POLYGON_API_KEY", "")
    if not polygon_api_key:
        print("Warning: POLYGON_API_KEY environment variable not set.")
    else:
        print("Starting Polygon MCP server with API key configured.")

    # Configure HTTP transport environment variables before server starts
    configure_http_transport()

    # Log transport configuration for debugging
    selected_transport = transport()
    print(f"Starting MCP server with transport: {selected_transport}")
    if selected_transport in ("sse", "streamable-http"):
        host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
        port = os.environ.get("FASTMCP_PORT", "8000")
        path = os.environ.get("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp")
        print(f"HTTP server will listen on: http://{host}:{port}{path}")

    server.run(transport=selected_transport)


if __name__ == "__main__":
    start_server()
