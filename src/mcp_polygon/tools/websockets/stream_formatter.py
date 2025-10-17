"""
Stream message formatting for WebSocket data.

Documentation References:
- Message Format: polygon-docs/websockets/INDEX_AGENT.md:123-156
- Field Reference: polygon-docs/websockets/INDEX_AGENT.md:382-475
"""

import json
from datetime import datetime


def format_stream_message(message: dict, pretty: bool = True) -> str:
    """
    Format a WebSocket message for LLM consumption.

    Args:
        message: Raw WebSocket message dict
        pretty: Whether to pretty-print JSON (default: True for readability)

    Returns:
        Formatted JSON string with key fields highlighted

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:123-156
    """
    event_type = message.get("ev", "UNKNOWN")

    # Add human-readable timestamp if present
    if "t" in message:
        timestamp_ms = message["t"]
        message["timestamp_readable"] = datetime.fromtimestamp(
            timestamp_ms / 1000
        ).isoformat()

    # Format based on event type
    if event_type == "T":  # Trade
        return _format_trade(message, pretty)
    elif event_type == "Q":  # Quote
        return _format_quote(message, pretty)
    elif event_type in ["AM", "XA", "CA"]:  # Aggregate Minute
        return _format_aggregate(message, "minute", pretty)
    elif event_type in ["A", "AS", "XAS", "CAS"]:  # Aggregate Second
        return _format_aggregate(message, "second", pretty)
    elif event_type == "V":  # Index Value
        return _format_index_value(message, pretty)
    elif event_type == "LULD":  # Limit Up/Limit Down
        return _format_luld(message, pretty)
    elif event_type == "FMV":  # Fair Market Value
        return _format_fmv(message, pretty)
    else:
        # Generic formatting for unknown types
        return json.dumps(message, indent=2 if pretty else None)


def _format_trade(trade: dict, pretty: bool) -> str:
    """
    Format trade message.

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:384-395
    """
    symbol = trade.get("sym", "UNKNOWN")
    price = trade.get("p", 0)
    size = trade.get("s", 0)

    summary = {
        "event": "TRADE",
        "symbol": symbol,
        "price": price,
        "size": size,
        "exchange_id": trade.get("x"),
        "conditions": trade.get("c", []),
        "timestamp": trade.get("timestamp_readable"),
        "full_data": trade,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def _format_quote(quote: dict, pretty: bool) -> str:
    """
    Format quote message.

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:397-412
    """
    symbol = quote.get("sym", "UNKNOWN")
    bid_price = quote.get("bp", 0)
    ask_price = quote.get("ap", 0)

    summary = {
        "event": "QUOTE",
        "symbol": symbol,
        "bid": {
            "price": bid_price,
            "size": quote.get("bs"),
            "exchange": quote.get("bx"),
        },
        "ask": {
            "price": ask_price,
            "size": quote.get("as"),
            "exchange": quote.get("ax"),
        },
        "spread": round(ask_price - bid_price, 4),
        "timestamp": quote.get("timestamp_readable"),
        "full_data": quote,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def _format_aggregate(agg: dict, timeframe: str, pretty: bool) -> str:
    """
    Format aggregate bar message (minute or second).

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:414-443
    """
    symbol = agg.get("sym", "UNKNOWN")

    summary = {
        "event": f"AGGREGATE_{timeframe.upper()}",
        "symbol": symbol,
        "open": agg.get("o"),
        "high": agg.get("h"),
        "low": agg.get("l"),
        "close": agg.get("c"),
        "volume": agg.get("v"),
        "accumulated_volume": agg.get("av"),
        "vwap": agg.get("vw"),
        "start_time": agg.get("s"),
        "end_time": agg.get("e"),
        "full_data": agg,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def _format_index_value(value: dict, pretty: bool) -> str:
    """
    Format index value message.

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:446-454
    """
    summary = {
        "event": "INDEX_VALUE",
        "symbol": value.get("sym"),
        "value": value.get("val"),
        "timestamp": value.get("timestamp_readable"),
        "full_data": value,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def _format_luld(luld: dict, pretty: bool) -> str:
    """
    Format LULD (Limit Up Limit Down) message.

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:456-465
    """
    summary = {
        "event": "LULD",
        "symbol": luld.get("sym"),
        "tier": luld.get("tier"),
        "halt": luld.get("halt"),
        "timestamp": luld.get("timestamp_readable"),
        "full_data": luld,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def _format_fmv(fmv: dict, pretty: bool) -> str:
    """
    Format Fair Market Value message.

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:467-475
    """
    summary = {
        "event": "FAIR_MARKET_VALUE",
        "symbol": fmv.get("sym"),
        "fair_value": fmv.get("fmv"),
        "timestamp": fmv.get("timestamp_readable"),
        "full_data": fmv,
    }

    return json.dumps(summary, indent=2 if pretty else None)


def format_status_message(status: dict) -> str:
    """
    Format connection status/error message.

    Args:
        status: Status dict from connection manager

    Returns:
        Formatted status message

    Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490
    """
    status_type = status.get("status", "UNKNOWN")
    message = status.get("message", "")

    if status_type == "connected":
        return f"✓ Connected to Polygon WebSocket: {message}"
    elif status_type == "auth_success":
        return f"✓ Authenticated successfully: {message}"
    elif status_type == "auth_failed":
        return f"✗ Authentication failed: {message}"
    elif status_type == "success":
        return f"✓ Success: {message}"
    elif status_type == "error":
        return f"✗ Error: {message}"
    else:
        return f"[{status_type.upper()}] {message}"


def format_connection_status(status: dict) -> str:
    """
    Format connection status for display.

    Args:
        status: Status dict from ConnectionManager.get_status()

    Returns:
        Formatted status string
    """
    state_emoji = {
        "connected": "✓",
        "connecting": "⟳",
        "authenticating": "🔐",
        "disconnected": "○",
        "error": "✗",
    }

    emoji = state_emoji.get(status["state"], "?")

    return f"""
{emoji} {status["market"].upper()} WebSocket
State: {status["state"]}
Endpoint: {status["endpoint"]}
Subscriptions: {status["subscription_count"]} channels
Channels: {", ".join(status["subscriptions"][:5])}{"..." if len(status["subscriptions"]) > 5 else ""}
""".strip()
