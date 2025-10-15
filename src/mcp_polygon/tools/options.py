"""Options-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict
from ..api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all options-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_snapshot_option(
        underlying_asset: str,
        option_contract: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get snapshot for a specific option contract.
        """
        return await api.call(
            "get_snapshot_option",
            underlying_asset=underlying_asset,
            option_contract=option_contract,
            params=params,
        )
