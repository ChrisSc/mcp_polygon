"""Economy-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, date
from ..api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all economy-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_treasury_yields(
        date: Optional[Union[str, datetime, date]] = None,
        date_any_of: Optional[str] = None,
        date_lt: Optional[Union[str, datetime, date]] = None,
        date_lte: Optional[Union[str, datetime, date]] = None,
        date_gt: Optional[Union[str, datetime, date]] = None,
        date_gte: Optional[Union[str, datetime, date]] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve treasury yield data.
        """
        return await api.call(
            "list_treasury_yields",
            date=date,
            date_any_of=date_any_of,
            date_lt=date_lt,
            date_lte=date_lte,
            date_gt=date_gt,
            date_gte=date_gte,
            limit=limit,
            sort=sort,
            order=order,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_inflation(
        date: Optional[Union[str, datetime, date]] = None,
        date_any_of: Optional[str] = None,
        date_gt: Optional[Union[str, datetime, date]] = None,
        date_gte: Optional[Union[str, datetime, date]] = None,
        date_lt: Optional[Union[str, datetime, date]] = None,
        date_lte: Optional[Union[str, datetime, date]] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get inflation data from the Federal Reserve.
        """
        return await api.call(
            "list_inflation",
            date=date,
            date_any_of=date_any_of,
            date_gt=date_gt,
            date_gte=date_gte,
            date_lt=date_lt,
            date_lte=date_lte,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_inflation_expectations(
        date: Optional[Union[str, datetime, date]] = None,
        date_any_of: Optional[str] = None,
        date_gt: Optional[Union[str, datetime, date]] = None,
        date_gte: Optional[Union[str, datetime, date]] = None,
        date_lt: Optional[Union[str, datetime, date]] = None,
        date_lte: Optional[Union[str, datetime, date]] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get survey-based inflation expectations data.

        Returns expected inflation rates for various time horizons based on consumer surveys.
        Provides forward-looking inflation expectations that can help predict economic trends.

        Args:
            date: Specific date (YYYY-MM-DD)
            date_any_of: Comma-separated dates
            date_gt: Greater than date
            date_gte: Greater than or equal to date
            date_lt: Less than date
            date_lte: Less than or equal to date
            limit: Max results (default 10, max 1000)
            sort: Sort field
            order: Sort order ("asc" or "desc")
            params: Additional query parameters

        Returns:
            CSV with columns: date, one_year, three_year, five_year (inflation expectations %)
        """
        return await api.call(
            "list_inflation_expectations",
            date=date,
            date_any_of=date_any_of,
            date_gt=date_gt,
            date_gte=date_gte,
            date_lt=date_lt,
            date_lte=date_lte,
            limit=limit,
            sort=sort,
            order=order,
            params=params,
        )
