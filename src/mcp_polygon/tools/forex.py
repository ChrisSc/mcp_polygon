"""Forex-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, date
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

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_forex_sma(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 50,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 10,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Simple Moving Average (SMA) technical indicator for a forex ticker (format: C:EURUSD)."""
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
    async def get_forex_ema(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 50,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 10,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Exponential Moving Average (EMA) technical indicator for a forex ticker (format: C:EURUSD)."""
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
    async def get_forex_macd(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        short_window: Optional[int] = None,
        long_window: Optional[int] = None,
        signal_window: Optional[int] = None,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 10,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Moving Average Convergence/Divergence (MACD) technical indicator for a forex ticker (format: C:EURUSD)."""
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
    async def get_forex_rsi(
        ticker: str,
        timestamp: Optional[Union[str, int, datetime, date]] = None,
        timespan: Optional[str] = None,
        adjusted: Optional[bool] = None,
        window: Optional[int] = 14,
        series_type: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = 10,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get Relative Strength Index (RSI) technical indicator for a forex ticker (format: C:EURUSD)."""
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
