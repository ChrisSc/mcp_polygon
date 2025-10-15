import os
import logging
import sys
from typing import Literal
from mcp.server.fastmcp import FastMCP
from polygon import RESTClient
from importlib.metadata import version, PackageNotFoundError
from .formatters import json_to_csv
from .tools import stocks, options, futures, crypto, forex, economy, indices

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

poly_mcp = FastMCP("Polygon", dependencies=["polygon"])

# Register all tools by asset class
stocks.register_tools(poly_mcp, polygon_client, json_to_csv)
options.register_tools(poly_mcp, polygon_client, json_to_csv)
futures.register_tools(poly_mcp, polygon_client, json_to_csv)
crypto.register_tools(poly_mcp, polygon_client, json_to_csv)
forex.register_tools(poly_mcp, polygon_client, json_to_csv)
economy.register_tools(poly_mcp, polygon_client, json_to_csv)
indices.register_tools(poly_mcp, polygon_client, json_to_csv)


def run(transport: Literal["stdio", "sse", "streamable-http"] = "stdio") -> None:
    """Run the Polygon MCP server."""
    poly_mcp.run(transport)
