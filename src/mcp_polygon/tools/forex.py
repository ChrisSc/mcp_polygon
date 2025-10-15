"""Forex-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict
from ..api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all forex-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_last_forex_quote(
        from_: str,
        to: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get the most recent forex quote.
        """
        return await api.call(
            "get_last_forex_quote",
            from_=from_,
            to=to,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_real_time_currency_conversion(
        from_: str,
        to: str,
        amount: Optional[float] = None,
        precision: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get real-time currency conversion.
        """
        return await api.call(
            "get_real_time_currency_conversion",
            from_=from_,
            to=to,
            amount=amount,
            precision=precision,
            params=params,
        )
