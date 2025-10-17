import os
import logging
import sys
from typing import Literal
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from polygon import RESTClient
from importlib.metadata import version, PackageNotFoundError
from .formatters import json_to_csv
from .tools.rest import stocks, options, futures, crypto, forex, economy, indices
from .tools.websockets.connection_manager import ConnectionManager
from .tools.websockets import (
    stocks as stocks_ws,
    crypto as crypto_ws,
    options as options_ws,
    futures as futures_ws,
    forex as forex_ws,
    indices as indices_ws,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],  # MCP uses stderr for logs
)
logger = logging.getLogger("mcp_polygon")

POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")
if not POLYGON_API_KEY:
    print("Warning: POLYGON_API_KEY environment variable not set.")

version_number = "MCP-Polygon/unknown"
try:
    version_number = f"MCP-Polygon/{version('mcp_polygon')}"
except PackageNotFoundError:
    pass

polygon_client = RESTClient(POLYGON_API_KEY)
polygon_client.headers["User-Agent"] += f" {version_number}"

# Create global ConnectionManager for WebSocket streaming
connection_manager = ConnectionManager()

# Configure transport security for HTTP transports
# This enables DNS rebinding protection as required by MCP specification
# Note: For local development, we allow localhost connections from Claude Code
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["localhost:8000", "127.0.0.1:8000", "0.0.0.0:8000"],
    allowed_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",  # Claude Code may use port-less origin
        "http://127.0.0.1",
    ],
)

# Read host and port from environment for HTTP transports
# Default to 127.0.0.1:8000 for stdio, 0.0.0.0:8000 for HTTP (Docker compatibility)
http_host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
http_port = int(os.environ.get("FASTMCP_PORT", "8000"))

poly_mcp = FastMCP(
    "Polygon",
    dependencies=["polygon"],
    transport_security=transport_security,
    host=http_host,
    port=http_port,
)

# Register REST API tools by asset class
stocks.register_tools(poly_mcp, polygon_client, json_to_csv)
options.register_tools(poly_mcp, polygon_client, json_to_csv)
futures.register_tools(poly_mcp, polygon_client, json_to_csv)
crypto.register_tools(poly_mcp, polygon_client, json_to_csv)
forex.register_tools(poly_mcp, polygon_client, json_to_csv)
economy.register_tools(poly_mcp, polygon_client, json_to_csv)
indices.register_tools(poly_mcp, polygon_client, json_to_csv)

# Register WebSocket streaming tools
stocks_ws.register_tools(poly_mcp, connection_manager)
crypto_ws.register_tools(poly_mcp, connection_manager)
options_ws.register_tools(poly_mcp, connection_manager)
futures_ws.register_tools(poly_mcp, connection_manager)
forex_ws.register_tools(poly_mcp, connection_manager)
indices_ws.register_tools(poly_mcp, connection_manager)


def run(transport: Literal["stdio", "sse", "streamable-http"] = "stdio") -> None:
    """Run the Polygon MCP server."""
    poly_mcp.run(transport)
