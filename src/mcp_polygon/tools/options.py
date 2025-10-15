"""Options-related MCP tools for Polygon.io API"""

from typing import Optional, Any, Dict, Union
from datetime import datetime, date
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

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_options_contracts(
        underlying_ticker: Optional[str] = None,
        contract_type: Optional[str] = None,
        expiration_date: Optional[Union[str, date]] = None,
        strike_price: Optional[float] = None,
        limit: Optional[int] = 100,
        order: Optional[str] = None,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        List all options contracts with optional filtering by underlying ticker, contract type, expiration date, and strike price.

        Contract type must be either "call" or "put" if specified.
        """
        return await api.call(
            "list_options_contracts",
            underlying_ticker=underlying_ticker,
            contract_type=contract_type,
            expiration_date=expiration_date,
            strike_price=strike_price,
            limit=limit,
            order=order,
            sort=sort,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_options_contract(
        options_ticker: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get detailed specifications for a specific options contract including strike price, expiration date, contract type, and exercise style.

        Options ticker format: O:SPY251219C00650000 (O: prefix + underlying + expiration YYMMDD + C/P + strike price * 1000)
        """
        return await api.call(
            "get_options_contract",
            ticker=options_ticker,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_options_chain(
        underlying_asset: str,
        strike_price: Optional[float] = None,
        expiration_date: Optional[Union[str, date]] = None,
        contract_type: Optional[str] = None,
        limit: Optional[int] = 250,
        order: Optional[str] = None,
        sort: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get the complete options chain for an underlying asset with optional filtering by strike price, expiration date, and contract type.

        Contract type must be either "call" or "put" if specified. Returns all contracts (calls and puts) by default.
        """
        return await api.call(
            "list_snapshot_options_chain",
            underlying_asset=underlying_asset,
            params=params,
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_options_sma(
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
        """Get Simple Moving Average (SMA) technical indicator for an options ticker (format: O:SPY251219C00650000)."""
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
    async def get_options_ema(
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
        """Get Exponential Moving Average (EMA) technical indicator for an options ticker (format: O:SPY251219C00650000)."""
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
    async def get_options_macd(
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
        """Get Moving Average Convergence/Divergence (MACD) technical indicator for an options ticker (format: O:SPY251219C00650000)."""
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
    async def get_options_rsi(
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
        """Get Relative Strength Index (RSI) technical indicator for an options ticker (format: O:SPY251219C00650000)."""
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
