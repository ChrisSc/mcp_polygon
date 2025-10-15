"""Futures-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import date
from ..api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all futures-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_aggregates(
        ticker: str,
        resolution: str,
        window_start: Optional[str] = None,
        window_start_lt: Optional[str] = None,
        window_start_lte: Optional[str] = None,
        window_start_gt: Optional[str] = None,
        window_start_gte: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get aggregates for a futures contract in a given time range.
        """
        return await api.call(
            "list_futures_aggregates",
            ticker=ticker,
            resolution=resolution,
            window_start=window_start,
            window_start_lt=window_start_lt,
            window_start_lte=window_start_lte,
            window_start_gt=window_start_gt,
            window_start_gte=window_start_gte,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_contracts(
        product_code: Optional[str] = None,
        first_trade_date: Optional[Union[str, date]] = None,
        last_trade_date: Optional[Union[str, date]] = None,
        as_of: Optional[Union[str, date]] = None,
        active: Optional[str] = None,
        type: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get a paginated list of futures contracts.
        """
        return await api.call(
            "list_futures_contracts",
            product_code=product_code,
            first_trade_date=first_trade_date,
            last_trade_date=last_trade_date,
            as_of=as_of,
            active=active,
            type=type,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_futures_contract_details(
        ticker: str,
        as_of: Optional[Union[str, date]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get details for a single futures contract at a specified point in time.
        """
        return await api.call(
            "get_futures_contract_details",
            ticker=ticker,
            as_of=as_of,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_products(
        name: Optional[str] = None,
        name_search: Optional[str] = None,
        as_of: Optional[Union[str, date]] = None,
        trading_venue: Optional[str] = None,
        sector: Optional[str] = None,
        sub_sector: Optional[str] = None,
        asset_class: Optional[str] = None,
        asset_sub_class: Optional[str] = None,
        type: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get a list of futures products (including combos).
        """
        return await api.call(
            "list_futures_products",
            name=name,
            name_search=name_search,
            as_of=as_of,
            trading_venue=trading_venue,
            sector=sector,
            sub_sector=sub_sector,
            asset_class=asset_class,
            asset_sub_class=asset_sub_class,
            type=type,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_futures_product_details(
        product_code: str,
        type: Optional[str] = None,
        as_of: Optional[Union[str, date]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get details for a single futures product as it was at a specific day.
        """
        return await api.call(
            "get_futures_product_details",
            product_code=product_code,
            type=type,
            as_of=as_of,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_quotes(
        ticker: str,
        timestamp: Optional[str] = None,
        timestamp_lt: Optional[str] = None,
        timestamp_lte: Optional[str] = None,
        timestamp_gt: Optional[str] = None,
        timestamp_gte: Optional[str] = None,
        session_end_date: Optional[str] = None,
        session_end_date_lt: Optional[str] = None,
        session_end_date_lte: Optional[str] = None,
        session_end_date_gt: Optional[str] = None,
        session_end_date_gte: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get quotes for a futures contract in a given time range.
        """
        return await api.call(
            "list_futures_quotes",
            ticker=ticker,
            timestamp=timestamp,
            timestamp_lt=timestamp_lt,
            timestamp_lte=timestamp_lte,
            timestamp_gt=timestamp_gt,
            timestamp_gte=timestamp_gte,
            session_end_date=session_end_date,
            session_end_date_lt=session_end_date_lt,
            session_end_date_lte=session_end_date_lte,
            session_end_date_gt=session_end_date_gt,
            session_end_date_gte=session_end_date_gte,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_trades(
        ticker: str,
        timestamp: Optional[str] = None,
        timestamp_lt: Optional[str] = None,
        timestamp_lte: Optional[str] = None,
        timestamp_gt: Optional[str] = None,
        timestamp_gte: Optional[str] = None,
        session_end_date: Optional[str] = None,
        session_end_date_lt: Optional[str] = None,
        session_end_date_lte: Optional[str] = None,
        session_end_date_gt: Optional[str] = None,
        session_end_date_gte: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get trades for a futures contract in a given time range.
        """
        return await api.call(
            "list_futures_trades",
            ticker=ticker,
            timestamp=timestamp,
            timestamp_lt=timestamp_lt,
            timestamp_lte=timestamp_lte,
            timestamp_gt=timestamp_gt,
            timestamp_gte=timestamp_gte,
            session_end_date=session_end_date,
            session_end_date_lt=session_end_date_lt,
            session_end_date_lte=session_end_date_lte,
            session_end_date_gt=session_end_date_gt,
            session_end_date_gte=session_end_date_gte,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_schedules(
        session_end_date: Optional[str] = None,
        trading_venue: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get trading schedules for multiple futures products on a specific date.
        """
        return await api.call(
            "list_futures_schedules",
            session_end_date=session_end_date,
            trading_venue=trading_venue,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_schedules_by_product_code(
        product_code: str,
        session_end_date: Optional[str] = None,
        session_end_date_lt: Optional[str] = None,
        session_end_date_lte: Optional[str] = None,
        session_end_date_gt: Optional[str] = None,
        session_end_date_gte: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get schedule data for a single futures product across many trading dates.
        """
        return await api.call(
            "list_futures_schedules_by_product_code",
            product_code=product_code,
            session_end_date=session_end_date,
            session_end_date_lt=session_end_date_lt,
            session_end_date_lte=session_end_date_lte,
            session_end_date_gt=session_end_date_gt,
            session_end_date_gte=session_end_date_gte,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_market_statuses(
        product_code_any_of: Optional[str] = None,
        product_code: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get market statuses for futures products.
        """
        return await api.call(
            "list_futures_market_statuses",
            product_code_any_of=product_code_any_of,
            product_code=product_code,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_futures_snapshot(
        ticker: Optional[str] = None,
        ticker_any_of: Optional[str] = None,
        ticker_gt: Optional[str] = None,
        ticker_gte: Optional[str] = None,
        ticker_lt: Optional[str] = None,
        ticker_lte: Optional[str] = None,
        product_code: Optional[str] = None,
        product_code_any_of: Optional[str] = None,
        product_code_gt: Optional[str] = None,
        product_code_gte: Optional[str] = None,
        product_code_lt: Optional[str] = None,
        product_code_lte: Optional[str] = None,
        limit: Optional[int] = 10,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get snapshots for futures contracts.
        """
        return await api.call(
            "get_futures_snapshot",
            ticker=ticker,
            ticker_any_of=ticker_any_of,
            ticker_gt=ticker_gt,
            ticker_gte=ticker_gte,
            ticker_lt=ticker_lt,
            ticker_lte=ticker_lte,
            product_code=product_code,
            product_code_any_of=product_code_any_of,
            product_code_gt=product_code_gt,
            product_code_gte=product_code_gte,
            product_code_lt=product_code_lt,
            product_code_lte=product_code_lte,
            limit=limit,
            sort=sort,
            params=params,
        )
