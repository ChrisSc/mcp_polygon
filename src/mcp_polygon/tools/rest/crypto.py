"""Crypto-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, date
from ...api_wrapper import PolygonAPIWrapper
from ...validation import validate_date


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

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_crypto_sma(
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
        """Get Simple Moving Average (SMA) technical indicator for a crypto ticker (format: X:BTCUSD)."""
        # Validate timestamp is not in future
        if error := validate_date(timestamp, "timestamp"):
            return error

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
    async def get_crypto_ema(
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
        """Get Exponential Moving Average (EMA) technical indicator for a crypto ticker (format: X:BTCUSD)."""
        # Validate timestamp is not in future
        if error := validate_date(timestamp, "timestamp"):
            return error

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
    async def get_crypto_macd(
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
        """Get Moving Average Convergence/Divergence (MACD) technical indicator for a crypto ticker (format: X:BTCUSD)."""
        # Validate timestamp is not in future
        if error := validate_date(timestamp, "timestamp"):
            return error

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
    async def get_crypto_rsi(
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
        """Get Relative Strength Index (RSI) technical indicator for a crypto ticker (format: X:BTCUSD)."""
        # Validate timestamp is not in future
        if error := validate_date(timestamp, "timestamp"):
            return error

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
