"""WebSocket streaming tools for Polygon.io"""

from .connection_manager import (
    WebSocketConnection,
    ConnectionManager,
    ConnectionState,
)
from .stream_formatter import (
    format_stream_message,
    format_status_message,
    format_connection_status,
)

# Phase 3: WebSocket tool modules (36 tools total, 6 per market)
from . import stocks, crypto, options, futures, forex, indices

__all__ = [
    "WebSocketConnection",
    "ConnectionManager",
    "ConnectionState",
    "format_stream_message",
    "format_status_message",
    "format_connection_status",
    "stocks",
    "crypto",
    "options",
    "futures",
    "forex",
    "indices",
]
