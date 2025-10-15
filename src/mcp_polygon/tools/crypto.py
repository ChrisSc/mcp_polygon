"""Crypto-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict
from ..api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all crypto-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_last_crypto_trade(
        from_: str,
        to: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get the most recent trade for a crypto pair.
        """
        return await api.call(
            "get_last_crypto_trade",
            from_=from_,
            to=to,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_snapshot_crypto_book(
        ticker: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get snapshot for a crypto ticker's order book.
        """
        return await api.call(
            "get_snapshot_crypto_book",
            ticker=ticker,
            params=params,
        )
