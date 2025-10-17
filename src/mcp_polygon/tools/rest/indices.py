"""Indices-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, date
from ...api_wrapper import PolygonAPIWrapper


def register_tools(mcp, client, formatter):
    """
    Register all indices-related tools with the MCP server.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_indices_snapshot(
        ticker_any_of: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 50,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get current snapshot of market indices values.

        Args:
            ticker_any_of: Comma-separated list of index tickers (e.g., "I:SPX,I:DJI,I:NDX")
            order: Sort order ("asc" or "desc")
            limit: Max results (default 10, max 250)
            sort: Sort field (e.g., "ticker")
            params: Additional parameters

        Returns:
            CSV with columns: ticker, session_open, session_high, session_low, session_close,
            prev_day_close, change, change_percent, updated

        Examples:
            - Get S&P 500 snapshot: ticker_any_of="I:SPX"
            - Get multiple indices: ticker_any_of="I:SPX,I:DJI,I:NDX"
        """
        return await api.call(
            "get_snapshot_indices",
            ticker_any_of=ticker_any_of,
            order=order,
            limit=limit,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_index_sma(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 50,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 50,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Simple Moving Average (SMA) technical indicator for an index ticker (format: I:SPX)."""
        return await api.call(
            "get_sma",
            ticker=ticker,
            timestamp=timestamp,
            timespan=timespan,
            adjusted=adjusted,
            window=window,
            series_type=series_type,
            order=order,
            limit=limit,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_index_ema(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 50,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 50,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Exponential Moving Average (EMA) technical indicator for an index ticker (format: I:SPX)."""
        return await api.call(
            "get_ema",
            ticker=ticker,
            timestamp=timestamp,
            timespan=timespan,
            adjusted=adjusted,
            window=window,
            series_type=series_type,
            order=order,
            limit=limit,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_index_macd(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        short_window: Optional[int] = None,
        long_window: Optional[int] = None,
        signal_window: Optional[int] = None,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 50,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Moving Average Convergence/Divergence (MACD) technical indicator for an index ticker (format: I:SPX)."""
        return await api.call(
            "get_macd",
            ticker=ticker,
            timestamp=timestamp,
            timespan=timespan,
            adjusted=adjusted,
            short_window=short_window,
            long_window=long_window,
            signal_window=signal_window,
            series_type=series_type,
            order=order,
            limit=limit,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_index_rsi(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 14,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 50,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Relative Strength Index (RSI) technical indicator for an index ticker (format: I:SPX)."""
        return await api.call(
            "get_rsi",
            ticker=ticker,
            timestamp=timestamp,
            timespan=timespan,
            adjusted=adjusted,
            window=window,
            series_type=series_type,
            order=order,
            limit=limit,
            params=params,
        )
