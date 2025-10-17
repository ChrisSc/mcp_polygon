# WebSocket Implementation Plan - MCP Polygon Server

**Version:** 1.0
**Date:** 2025-10-17
**Status:** Planning Phase
**Branch:** websockets-planning

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Documentation Cross-Reference Requirements](#documentation-cross-reference-requirements)
- [WebSocket Channels Overview](#websocket-channels-overview)
- [Phase 1: Server Reorganization](#phase-1-server-reorganization-weeks-1-2)
- [Phase 2: WebSocket Infrastructure](#phase-2-websocket-infrastructure-weeks-3-4)
- [Phase 3: WebSocket Tools Implementation](#phase-3-websocket-tools-implementation-weeks-5-8)
- [Phase 4: Testing Strategy](#phase-4-testing-strategy-weeks-9-10)
- [Phase 5: Documentation & Polish](#phase-5-documentation--polish-weeks-11-12)
- [Implementation Timeline](#implementation-timeline)
- [Risk Mitigation](#risk-mitigation)
- [Success Criteria](#success-criteria)

---

## Executive Summary

This plan outlines the implementation of **WebSocket streaming endpoints** for the Polygon MCP server, building upon the existing REST API foundation (81 tools, 99% endpoint coverage). The implementation will add **real-time streaming capabilities** across 6 asset classes while maintaining the production-ready quality and architectural patterns of the current system.

**Key Objectives:**
- Add ~36 WebSocket streaming tools across 6 markets
- Maintain existing REST API functionality (zero regression)
- Implement robust connection management with auto-reconnect
- Provide LLM-friendly streaming data format
- Achieve 90%+ test coverage on new code
- Complete in 12 weeks

**Architectural Principle:** WebSocket tools are fundamentally different from REST tools - they manage persistent connections and subscriptions rather than one-shot requests.

---

## Documentation Cross-Reference Requirements

### Lesson from REST API Implementation

During REST API implementation, we encountered hallucinated parameters that caused SDK compliance issues. To prevent this with WebSocket tools, **every tool must include documentation cross-references** in its docstring.

### Required Documentation Pattern

```python
@mcp.tool()
async def start_stocks_stream(
    channels: List[str],
    api_key: Optional[str] = None,
    endpoint: str = "wss://socket.polygon.io/stocks"
) -> str:
    """
    Start real-time stock market data stream.

    Documentation References:
    - Connection: polygon-docs/websockets/quickstart.md:65-103
    - Stocks Overview: polygon-docs/websockets/stocks/overview.md:90-117
    - Trades Channel: polygon-docs/websockets/stocks/trades.md:1-50
    - Quotes Channel: polygon-docs/websockets/stocks/quotes.md:1-50
    - Minute Agg Channel: polygon-docs/websockets/stocks/aggregates-per-minute.md:1-50
    - Second Agg Channel: polygon-docs/websockets/stocks/aggregates-per-second.md:1-50
    - LULD Channel: polygon-docs/websockets/stocks/luld.md:1-50
    - FMV Channel: polygon-docs/websockets/stocks/fair-market-value.md:1-50

    Args:
        channels: List of channels to subscribe to. Format: "CHANNEL.SYMBOL"
                 Examples: ["T.AAPL", "Q.MSFT", "AM.*"]
                 Channel prefixes: T (trades), Q (quotes), AM (minute agg),
                                  A (second agg), LULD (halts), FMV (fair value)
        api_key: Polygon API key (uses POLYGON_API_KEY env var if not provided)
        endpoint: WebSocket endpoint (default: real-time, use delayed.polygon.io for 15-min delay)

    Returns:
        Status message indicating stream started and connection details
    """
```

### Documentation Structure Reference

```
polygon-docs/websockets/
├── INDEX_AGENT.md                    # Master navigation (lines 1-824)
├── quickstart.md                      # Connection guide (lines 1-1176)
├── README.md                          # Overview and best practices
│
├── stocks/
│   ├── overview.md                   # Market overview and architecture (lines 1-343)
│   ├── trades.md                     # T.* channel - Trade executions
│   ├── quotes.md                     # Q.* channel - NBBO quotes
│   ├── aggregates-per-minute.md      # AM.* channel - Minute OHLC bars
│   ├── aggregates-per-second.md      # A.* channel - Second OHLC bars
│   ├── luld.md                       # LULD.* channel - Trading halts
│   └── fair-market-value.md          # FMV.* channel - Fair market value
│
├── options/
│   ├── overview.md
│   ├── trades.md                     # T.O:* channel
│   ├── quotes.md                     # Q.O:* channel (1000 contract limit)
│   ├── aggregates-per-minute.md      # AM.O:* channel
│   ├── aggregates-per-second.md      # AS.O:* channel
│   └── fair-market-value.md          # FMV.O:* channel
│
├── futures/
│   ├── overview.md                   # Beta status, exchange info
│   ├── trades.md                     # T.* channel
│   ├── quotes.md                     # Q.* channel
│   ├── aggregates-per-minute.md      # AM.* channel
│   └── aggregates-per-second.md      # AS.* channel
│
├── indices/
│   ├── overview.md
│   ├── value.md                      # V.I:* channel - Index values
│   ├── aggregates-per-minute.md      # AM.I:* channel
│   └── aggregates-per-second.md      # AS.I:* channel (Business only)
│
├── forex/
│   ├── overview.md                   # 24/5 market characteristics
│   ├── quotes.md                     # C.* channel
│   ├── aggregates-per-minute.md      # CA.* channel
│   ├── aggregates-per-second.md      # CAS.* channel
│   └── fair-market-value.md          # FMV.* channel (Business only)
│
└── crypto/
    ├── overview.md                   # 24/7 market
    ├── trades.md                     # XT.* channel
    ├── quotes.md                     # XQ.* channel
    ├── aggregates-per-minute.md      # XA.* channel
    ├── aggregates-per-second.md      # XAS.* channel
    └── fair-market-value.md          # FMV.* channel (Business only)
```

### Validation Process

**During Development:**
1. Developer writes tool with doc references
2. Agent validates references point to valid files and line ranges
3. Agent verifies channel prefixes match documentation
4. Agent checks parameter names match Polygon SDK

**During Review:**
1. Code reviewer verifies all doc references are present
2. Code reviewer spot-checks 3 random references for accuracy
3. CI/CD fails if doc file paths don't exist

---

## WebSocket Channels Overview

### Channel Format by Market

Based on **polygon-docs/websockets/INDEX_AGENT.md:52-62**:

| Market | Endpoint | Trades | Quotes | Min Agg | Sec Agg | Unique Channels | Trading Hours |
|--------|----------|--------|--------|---------|---------|-----------------|---------------|
| **Stocks** | `wss://socket.polygon.io/stocks` | T.* | Q.* | AM.* | A.* | LULD.*, FMV.* | 9:30 AM - 4:00 PM ET + Extended |
| **Options** | `wss://socket.polygon.io/options` | T.O:* | Q.O:* | AM.O:* | AS.O:* | FMV.O:* | 9:30 AM - 4:00 PM ET |
| **Futures** | `wss://socket.polygon.io/futures` | T.* | Q.* | AM.* | AS.* | None | ~24/5 (varies by exchange) |
| **Indices** | `wss://socket.polygon.io/indices` | N/A | N/A | AM.I:* | AS.I:* | V.I:* (values) | 9:30 AM - 4:00 PM ET |
| **Forex** | `wss://socket.polygon.io/forex` | N/A | C.* | CA.* | CAS.* | FMV.* | 24/5 |
| **Crypto** | `wss://socket.polygon.io/crypto` | XT.* | XQ.* | XA.* | XAS.* | FMV.* | 24/7 |

**Delayed Data Endpoints:** Replace `socket.polygon.io` with `delayed.polygon.io` for 15-minute delayed data.

### Subscription Pattern Examples

From **polygon-docs/websockets/INDEX_AGENT.md:94-119**:

```json
// Single ticker
{"action":"subscribe","params":"T.AAPL"}

// Multiple tickers
{"action":"subscribe","params":"T.AAPL,Q.AAPL,AM.MSFT"}

// Wildcard (all tickers - extreme volume)
{"action":"subscribe","params":"T.*"}

// Mixed markets
{"action":"subscribe","params":"T.AAPL,XT.BTC-USD,C.EUR/USD"}

// Unsubscribe
{"action":"unsubscribe","params":"T.AAPL"}
```

### Connection Flow

From **polygon-docs/websockets/INDEX_AGENT.md:69-90**:

```
1. Establish WebSocket → wss://socket.polygon.io/{market-type}
2. Authenticate → {"action":"auth","params":"API_KEY"}
3. Wait for Auth Success → [{"ev":"status","status":"auth_success"}]
4. Subscribe to Channels → {"action":"subscribe","params":"CHANNEL_LIST"}
5. Receive Data Stream → [{ev:"T",sym:"AAPL",p:150.25,...}]
```

### Message Format

From **polygon-docs/websockets/INDEX_AGENT.md:123-156**:

All messages are JSON arrays:
```json
[
  {
    "ev": "event_type",
    "sym": "symbol",
    // Additional fields specific to event type
  }
]
```

---

## Phase 1: Server Reorganization (Weeks 1-2)

### 1.1 Directory Structure Migration

**Goal:** Separate REST and WebSocket tools without breaking existing functionality.

**Current Structure:**
```
src/mcp_polygon/
├── __init__.py
├── server.py
├── api_wrapper.py
├── formatters.py
└── tools/
    ├── __init__.py
    ├── stocks.py (47 tools)
    ├── options.py (9 tools)
    ├── futures.py (11 tools)
    ├── crypto.py (7 tools)
    ├── forex.py (6 tools)
    ├── economy.py (3 tools)
    └── indices.py (5 tools)
```

**New Structure:**
```
src/mcp_polygon/
├── __init__.py
├── server.py (updated imports)
├── api_wrapper.py (REST only)
├── formatters.py (CSV for REST)
└── tools/
    ├── __init__.py
    ├── rest/
    │   ├── __init__.py
    │   ├── stocks.py (47 REST tools)
    │   ├── options.py (9 REST tools)
    │   ├── futures.py (11 REST tools)
    │   ├── crypto.py (7 REST tools)
    │   ├── forex.py (6 REST tools)
    │   ├── economy.py (3 REST tools)
    │   └── indices.py (5 REST tools)
    └── websockets/
        ├── __init__.py
        ├── connection_manager.py (NEW)
        ├── stream_formatter.py (NEW)
        ├── stocks.py (6 WS tools)
        ├── options.py (6 WS tools)
        ├── futures.py (6 WS tools)
        ├── indices.py (6 WS tools)
        ├── forex.py (6 WS tools)
        └── crypto.py (6 WS tools)
```

### 1.2 Migration Steps

**Step 1.1: Create Directory Structure**
```bash
mkdir -p src/mcp_polygon/tools/rest
mkdir -p src/mcp_polygon/tools/websockets
```

**Step 1.2: Move REST Tools**
```bash
# Move all existing tool files to rest/
mv src/mcp_polygon/tools/*.py src/mcp_polygon/tools/rest/
# Restore __init__.py
mv src/mcp_polygon/tools/rest/__init__.py src/mcp_polygon/tools/
```

**Step 1.3: Update Imports in server.py**

**Before:**
```python
from .tools import stocks, options, futures, crypto, forex, economy, indices
```

**After:**
```python
from .tools.rest import stocks, options, futures, crypto, forex, economy, indices
```

**Step 1.4: Update Import Statements in Tool Files**

In each `tools/rest/*.py` file:

**Before:**
```python
from ..api_wrapper import PolygonAPIWrapper
```

**After:**
```python
from ...api_wrapper import PolygonAPIWrapper
```

**Step 1.5: Create tools/rest/__init__.py**
```python
"""REST API tools for Polygon.io"""

__all__ = ['stocks', 'options', 'futures', 'crypto', 'forex', 'economy', 'indices']
```

**Step 1.6: Create tools/websockets/__init__.py**
```python
"""WebSocket streaming tools for Polygon.io"""

__all__ = ['stocks', 'options', 'futures', 'crypto', 'forex', 'indices']
```

### 1.3 Validation

**After migration, verify:**

1. **Server loads correctly:**
```bash
source venv/bin/activate
python -c "from src.mcp_polygon.server import poly_mcp; print(f'✅ {len(poly_mcp._tool_manager._tools)} tools loaded (expected: 81)')"
```

2. **All tests pass:**
```bash
pytest tests/ -v
```

3. **MCP Inspector works:**
```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon
```

4. **Smoke test REST endpoint:**
```python
# Test one tool from each market
await get_aggs("AAPL", 1, "day", "2024-01-01", "2024-01-31")
await get_snapshot_option("SPY", "O:SPY251219C00650000")
# ... etc
```

### 1.4 Update CLAUDE.md

Update module organization section:
```markdown
## Module Organization

src/mcp_polygon/
├── server.py          # Main orchestrator (49 lines)
├── api_wrapper.py     # REST API wrapper (170 lines)
├── formatters.py      # CSV output utilities (82 lines)
└── tools/             # API endpoints
    ├── rest/          # 81 REST tools (Phase 1-3)
    │   ├── stocks.py      # 47 tools
    │   ├── options.py     # 9 tools
    │   └── ... (5 more)
    └── websockets/    # 36 WebSocket tools (Phase 4)
        ├── connection_manager.py
        ├── stream_formatter.py
        ├── stocks.py      # 6 tools
        └── ... (5 more)
```

---

## Phase 2: WebSocket Infrastructure (Weeks 3-4)

### 2.1 Connection Manager Design

**File:** `src/mcp_polygon/tools/websockets/connection_manager.py`

**Documentation:** Based on polygon-docs/websockets/quickstart.md:65-241 and INDEX_AGENT.md:479-519

**Purpose:** Centralized WebSocket connection lifecycle management with:
- Connection pooling (one connection per market)
- Authentication handling
- Automatic reconnection with exponential backoff
- Subscription state tracking
- Message routing
- Error handling and logging

**Architecture:**

```python
"""
WebSocket connection management for Polygon.io streaming data.

Documentation References:
- Connection Flow: polygon-docs/websockets/quickstart.md:65-103
- Authentication: polygon-docs/websockets/quickstart.md:146-241
- Best Practices: polygon-docs/websockets/INDEX_AGENT.md:479-519
- Error Handling: polygon-docs/websockets/INDEX_AGENT.md:479-547
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Set
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    ERROR = "error"


class WebSocketConnection:
    """
    Manages a single WebSocket connection to a Polygon.io market endpoint.

    Handles connection lifecycle, authentication, subscriptions, and message routing.
    Implements automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s).

    Documentation: polygon-docs/websockets/quickstart.md:65-241
    """

    def __init__(self, market: str, endpoint: str, api_key: str):
        """
        Initialize WebSocket connection for a market.

        Args:
            market: Market type (stocks, options, futures, indices, forex, crypto)
            endpoint: WebSocket URL (e.g., wss://socket.polygon.io/stocks)
            api_key: Polygon API key for authentication
        """
        self.market = market
        self.endpoint = endpoint
        self.api_key = api_key
        self.websocket = None
        self.state = ConnectionState.DISCONNECTED
        self.subscriptions: Set[str] = set()
        self.message_handlers: List[Callable] = []
        self.reconnect_attempts = 0
        self.max_reconnect_delay = 30

    async def connect(self) -> None:
        """
        Establish WebSocket connection and authenticate.

        Documentation: polygon-docs/websockets/quickstart.md:65-92
        """
        try:
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to {self.endpoint}")

            self.websocket = await websockets.connect(
                self.endpoint,
                ping_interval=30,
                ping_timeout=10
            )

            self.state = ConnectionState.AUTHENTICATING
            await self._authenticate()

            # Start message receiver task
            asyncio.create_task(self._receive_messages())

            # Resubscribe to previous channels if reconnecting
            if self.subscriptions:
                await self._resubscribe()

            self.reconnect_attempts = 0
            self.state = ConnectionState.CONNECTED
            logger.info(f"✓ Connected to {self.market} WebSocket")

        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Connection failed: {e}")
            await self._handle_connection_error(e)

    async def _authenticate(self) -> None:
        """
        Send authentication message and wait for success.

        Documentation: polygon-docs/websockets/quickstart.md:146-175
        """
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        await self.websocket.send(json.dumps(auth_message))
        logger.debug("→ Authentication message sent")

        # Wait for auth success
        response = await self.websocket.recv()
        messages = json.loads(response)

        for msg in messages:
            if msg.get("ev") == "status":
                if msg.get("status") == "auth_success":
                    logger.info("✓ Authentication successful")
                    return
                elif msg.get("status") == "auth_failed":
                    raise Exception(f"Authentication failed: {msg.get('message')}")

        raise Exception("No authentication response received")

    async def subscribe(self, channels: List[str]) -> None:
        """
        Subscribe to data channels.

        Args:
            channels: List of channel subscriptions (e.g., ["T.AAPL", "Q.MSFT"])

        Documentation: polygon-docs/websockets/quickstart.md:245-278
        """
        if self.state != ConnectionState.CONNECTED:
            raise Exception(f"Cannot subscribe: connection state is {self.state.value}")

        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(channels)
        }
        await self.websocket.send(json.dumps(subscribe_message))

        self.subscriptions.update(channels)
        logger.info(f"→ Subscribed to {len(channels)} channels")

    async def unsubscribe(self, channels: List[str]) -> None:
        """
        Unsubscribe from data channels.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119
        """
        if self.state != ConnectionState.CONNECTED:
            raise Exception(f"Cannot unsubscribe: connection state is {self.state.value}")

        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ",".join(channels)
        }
        await self.websocket.send(json.dumps(unsubscribe_message))

        self.subscriptions.difference_update(channels)
        logger.info(f"→ Unsubscribed from {len(channels)} channels")

    async def _resubscribe(self) -> None:
        """Resubscribe to all channels after reconnection."""
        if self.subscriptions:
            logger.info(f"Resubscribing to {len(self.subscriptions)} channels")
            await self.subscribe(list(self.subscriptions))

    async def _receive_messages(self) -> None:
        """
        Receive and route WebSocket messages.

        Documentation: polygon-docs/websockets/quickstart.md:363-441
        """
        try:
            async for message in self.websocket:
                try:
                    messages = json.loads(message)

                    if not isinstance(messages, list):
                        logger.warning(f"Non-array message received: {message}")
                        continue

                    for msg in messages:
                        # Handle status messages
                        if msg.get("ev") == "status":
                            self._handle_status(msg)
                        else:
                            # Route market data to handlers
                            for handler in self.message_handlers:
                                await handler(msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {message}, error: {e}")

        except ConnectionClosed as e:
            logger.warning(f"Connection closed: {e}")
            await self._handle_connection_error(e)

    def _handle_status(self, status_msg: dict) -> None:
        """Handle WebSocket status messages."""
        status = status_msg.get("status")
        message = status_msg.get("message", "")
        logger.info(f"[STATUS] {status}: {message}")

    async def _handle_connection_error(self, error: Exception) -> None:
        """
        Handle connection errors with exponential backoff reconnection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:492-497
        """
        self.state = ConnectionState.ERROR

        # Calculate backoff delay (1s, 2s, 4s, 8s, ... max 30s)
        delay = min(2 ** self.reconnect_attempts, self.max_reconnect_delay)
        self.reconnect_attempts += 1

        logger.warning(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts})")
        await asyncio.sleep(delay)

        try:
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            # Will try again with increased delay
            await self._handle_connection_error(e)

    async def close(self) -> None:
        """Close WebSocket connection gracefully."""
        if self.websocket:
            await self.websocket.close()
            self.state = ConnectionState.DISCONNECTED
            logger.info(f"✓ Closed {self.market} WebSocket")

    def add_message_handler(self, handler: Callable) -> None:
        """Add a message handler callback."""
        self.message_handlers.append(handler)

    def get_status(self) -> dict:
        """Get connection status."""
        return {
            "market": self.market,
            "state": self.state.value,
            "endpoint": self.endpoint,
            "subscriptions": list(self.subscriptions),
            "subscription_count": len(self.subscriptions)
        }


class ConnectionManager:
    """
    Global manager for all WebSocket connections.

    Maintains one connection per market, handles lifecycle, and provides
    connection access to tools.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.connections: Dict[str, WebSocketConnection] = {}

    def get_connection(
        self,
        market: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> WebSocketConnection:
        """
        Get or create a connection for a market.

        Args:
            market: Market type (stocks, options, futures, indices, forex, crypto)
            endpoint: WebSocket endpoint (auto-generated if not provided)
            api_key: API key (required for first connection to market)

        Returns:
            WebSocketConnection instance
        """
        if market in self.connections:
            return self.connections[market]

        # Create new connection
        if not endpoint:
            endpoint = f"wss://socket.polygon.io/{market}"
        if not api_key:
            raise ValueError(f"API key required for first connection to {market}")

        connection = WebSocketConnection(market, endpoint, api_key)
        self.connections[market] = connection
        return connection

    async def close_all(self) -> None:
        """Close all WebSocket connections."""
        for connection in self.connections.values():
            await connection.close()
        self.connections.clear()
        logger.info("✓ Closed all WebSocket connections")

    def get_all_statuses(self) -> List[dict]:
        """Get status of all connections."""
        return [conn.get_status() for conn in self.connections.values()]
```

### 2.2 Stream Formatter Design

**File:** `src/mcp_polygon/tools/websockets/stream_formatter.py`

**Documentation:** Based on polygon-docs/websockets/INDEX_AGENT.md:123-156 and 382-475

**Purpose:** Format WebSocket messages for LLM consumption (JSON format, not CSV).

**Rationale for JSON (not CSV):**
1. Real-time data needs timestamps and metadata preserved
2. LLMs handle streaming JSON efficiently
3. CSV requires buffering multiple messages (defeats real-time purpose)
4. JSON preserves data types (floats, ints, booleans)
5. Nested structures (conditions, Greeks) require JSON

```python
"""
Stream message formatting for WebSocket data.

Documentation References:
- Message Format: polygon-docs/websockets/INDEX_AGENT.md:123-156
- Field Reference: polygon-docs/websockets/INDEX_AGENT.md:382-475
"""

import json
from typing import Dict, Any, List
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
        "full_data": trade
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
            "exchange": quote.get("bx")
        },
        "ask": {
            "price": ask_price,
            "size": quote.get("as"),
            "exchange": quote.get("ax")
        },
        "spread": round(ask_price - bid_price, 4),
        "timestamp": quote.get("timestamp_readable"),
        "full_data": quote
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
        "full_data": agg
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
        "full_data": value
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
        "full_data": luld
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
        "full_data": fmv
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
        "error": "✗"
    }

    emoji = state_emoji.get(status["state"], "?")

    return f"""
{emoji} {status['market'].upper()} WebSocket
State: {status['state']}
Endpoint: {status['endpoint']}
Subscriptions: {status['subscription_count']} channels
Channels: {', '.join(status['subscriptions'][:5])}{'...' if len(status['subscriptions']) > 5 else ''}
""".strip()
```

---

## Phase 3: WebSocket Tools Implementation (Weeks 5-8)

### 3.1 Tool Architecture

**Key Difference from REST Tools:**

| Aspect | REST Tools | WebSocket Tools |
|--------|-----------|-----------------|
| Pattern | Request → Response | Connection management |
| Return | Single CSV dataset | Status message + stream |
| Duration | Milliseconds | Continuous until stopped |
| State | Stateless | Stateful (connection + subs) |
| Error Handling | Per-request | Connection-level |

### 3.2 Tool Categories (Per Market)

**1. Connection Tools:**
- `start_{market}_stream(channels, api_key, endpoint)` → Start streaming
- `stop_{market}_stream()` → Stop streaming
- `get_{market}_stream_status()` → Check connection status

**2. Subscription Tools:**
- `subscribe_{market}_channels(channels)` → Add subscriptions
- `unsubscribe_{market}_channels(channels)` → Remove subscriptions
- `list_{market}_subscriptions()` → Show active subscriptions

**Total:** 6 tools/market × 6 markets = **36 WebSocket tools**

### 3.3 Implementation Pattern (Stocks Example)

**File:** `src/mcp_polygon/tools/websockets/stocks.py`

```python
"""
WebSocket streaming tools for stocks market.

Documentation References:
- Stocks Overview: polygon-docs/websockets/stocks/overview.md:1-343
- Connection Guide: polygon-docs/websockets/quickstart.md:1-1176
- Channel Reference: polygon-docs/websockets/INDEX_AGENT.md:29-48
"""

import os
from typing import List, Optional
from mcp.types import ToolAnnotations
from .connection_manager import ConnectionManager
from .stream_formatter import format_stream_message, format_connection_status


def register_tools(mcp, connection_manager: ConnectionManager):
    """
    Register WebSocket streaming tools for stocks market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_stocks_stream(
        channels: List[str],
        api_key: Optional[str] = None,
        endpoint: str = "wss://socket.polygon.io/stocks"
    ) -> str:
        """
        Start real-time stock market data stream.

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Stocks Overview: polygon-docs/websockets/stocks/overview.md:90-117
        - Trades Channel (T.*): polygon-docs/websockets/stocks/trades.md:1-50
        - Quotes Channel (Q.*): polygon-docs/websockets/stocks/quotes.md:1-50
        - Minute Agg (AM.*): polygon-docs/websockets/stocks/aggregates-per-minute.md:1-50
        - Second Agg (A.*): polygon-docs/websockets/stocks/aggregates-per-second.md:1-50
        - LULD (LULD.*): polygon-docs/websockets/stocks/luld.md:1-50
        - FMV (FMV.*): polygon-docs/websockets/stocks/fair-market-value.md:1-50

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.SYMBOL"
                     Examples: ["T.AAPL", "Q.MSFT", "AM.*"]
                     Prefixes: T (trades), Q (quotes), AM (minute agg), A (second agg),
                              LULD (halts), FMV (fair value)
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: real-time)
                     Use "wss://delayed.polygon.io/stocks" for 15-min delayed data

        Returns:
            Status message indicating stream started

        Examples:
            - start_stocks_stream(["T.AAPL", "Q.AAPL"])
              → Stream Apple trades and quotes
            - start_stocks_stream(["AM.*"])
              → Stream all minute aggregates (high volume!)
            - start_stocks_stream(["T.AAPL", "T.MSFT", "T.TSLA"])
              → Stream trades for multiple symbols
        """
        # Get or create connection
        conn = connection_manager.get_connection(
            "stocks",
            endpoint=endpoint,
            api_key=api_key or os.getenv("POLYGON_API_KEY")
        )

        # Connect and authenticate
        await conn.connect()

        # Subscribe to channels
        await conn.subscribe(channels)

        return f"""✓ Started stocks WebSocket stream
Endpoint: {endpoint}
Channels: {', '.join(channels)}
State: {conn.state.value}

Stream is now active. Messages will be delivered as market data arrives.
Use stop_stocks_stream() to terminate the connection."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_stocks_stream() -> str:
        """
        Stop stock market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        conn = connection_manager.get_connection("stocks")
        await conn.close()

        return "✓ Stopped stocks WebSocket stream"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_stocks_stream_status() -> str:
        """
        Get current status of stocks WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("stocks")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active stocks WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_stocks_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active stocks stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["T.NVDA", "Q.AMD"])

        Returns:
            Confirmation message with updated subscription list
        """
        conn = connection_manager.get_connection("stocks")
        await conn.subscribe(channels)

        status = conn.get_status()
        return f"""✓ Added {len(channels)} subscriptions to stocks stream
Total subscriptions: {status['subscription_count']}
Channels: {', '.join(status['subscriptions'][:10])}{'...' if len(status['subscriptions']) > 10 else ''}"""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_stocks_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active stocks stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["T.AAPL"])

        Returns:
            Confirmation message with updated subscription list
        """
        conn = connection_manager.get_connection("stocks")
        await conn.unsubscribe(channels)

        status = conn.get_status()
        return f"""✓ Removed {len(channels)} subscriptions from stocks stream
Total subscriptions: {status['subscription_count']}
Channels: {', '.join(status['subscriptions'][:10])}{'...' if len(status['subscriptions']) > 10 else ''}"""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_stocks_subscriptions() -> str:
        """
        List all active subscriptions for stocks stream.

        Returns:
            List of subscribed channels
        """
        try:
            conn = connection_manager.get_connection("stocks")
            status = conn.get_status()

            if not status['subscriptions']:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status['subscriptions']:
                prefix = channel.split('.')[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Stocks Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    'T': 'Trades',
                    'Q': 'Quotes',
                    'AM': 'Minute Aggregates',
                    'A': 'Second Aggregates',
                    'LULD': 'Limit Up/Limit Down',
                    'FMV': 'Fair Market Value'
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active stocks WebSocket connection"
```

### 3.4 Tool Implementation Order

**Week 5: Core Markets**
1. Stocks (highest priority, most used)
2. Crypto (24/7 market, good for testing)

**Week 6: Derivatives**
3. Options (complex symbol format)
4. Futures (Beta status, careful testing)

**Week 7: Other Markets**
5. Forex (24/5 market)
6. Indices (requires Indices plan tier)

**Week 8: Integration & Refinement**
- Cross-market testing
- Error handling improvements
- Performance optimization
- Documentation review

### 3.5 Market-Specific Implementation Notes

**Options** (`tools/websockets/options.py`):
- Symbol format: `O:ROOT YYMMDDCP PPPPPPPP` (e.g., `O:SPY251219C00650000`)
- Documentation: polygon-docs/websockets/options/overview.md
- Channels: T.O:*, Q.O:*, AM.O:*, AS.O:*, FMV.O:*
- Note: Q.O:* has 1000 contract limit per subscription

**Futures** (`tools/websockets/futures.py`):
- Symbol format: `ROOTMYY` (e.g., `ESZ24`)
- Documentation: polygon-docs/websockets/futures/overview.md
- Status: Beta (may have limited availability)
- Channels: T.*, Q.*, AM.*, AS.*

**Indices** (`tools/websockets/indices.py`):
- Symbol format: `I:SYMBOL` (e.g., `I:SPX`)
- Documentation: polygon-docs/websockets/indices/overview.md
- Requires: Indices API tier
- Channels: V.I:* (values), AM.I:*, AS.I:*
- Unique: V.I:* provides real-time index calculations

**Forex** (`tools/websockets/forex.py`):
- Symbol format: `FROM/TO` (e.g., `EUR/USD`)
- Documentation: polygon-docs/websockets/forex/overview.md
- Hours: 24/5 (closed weekends)
- Channels: C.* (quotes), CA.* (minute agg), CAS.* (second agg), FMV.*

**Crypto** (`tools/websockets/crypto.py`):
- Symbol format: `FROM-TO` (e.g., `BTC-USD`)
- Documentation: polygon-docs/websockets/crypto/overview.md
- Hours: 24/7
- Channels: XT.* (trades), XQ.* (quotes), XA.* (minute agg), XAS.* (second agg), FMV.*

---

## Phase 4: Testing Strategy (Weeks 9-10)

### 4.1 Test Structure

```
tests/
├── test_rest_endpoints.py (existing - 54 tests)
├── test_api_wrapper.py (existing - 24 tests)
├── test_formatters.py (existing - 28 tests)
├── test_websockets/
│   ├── __init__.py
│   ├── conftest.py (shared fixtures)
│   ├── test_connection_manager.py (25 tests)
│   ├── test_stream_formatter.py (20 tests)
│   ├── test_stocks_ws.py (15 tests)
│   ├── test_options_ws.py (10 tests)
│   ├── test_futures_ws.py (10 tests)
│   ├── test_indices_ws.py (10 tests)
│   ├── test_forex_ws.py (10 tests)
│   ├── test_crypto_ws.py (10 tests)
│   └── test_integration_ws.py (10 tests)
```

**Target:** 120 new tests, 90%+ coverage on WebSocket code

### 4.2 Test Categories

**Unit Tests (Mocked WebSocket):**

`test_connection_manager.py` (25 tests):
```python
"""
Tests for WebSocket connection management.

Mocks WebSocket connections to test lifecycle, auth, subscriptions.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.mcp_polygon.tools.websockets.connection_manager import (
    WebSocketConnection,
    ConnectionManager,
    ConnectionState
)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connection_initialization():
    """Test connection initializes with correct state."""
    conn = WebSocketConnection("stocks", "wss://test.com", "test_key")
    assert conn.state == ConnectionState.DISCONNECTED
    assert conn.market == "stocks"
    assert len(conn.subscriptions) == 0


@pytest.mark.asyncio
async def test_authentication_success(mock_websocket):
    """Test successful authentication flow."""
    # Mock auth success response
    mock_websocket.recv.return_value = '[{"ev":"status","status":"auth_success"}]'

    with patch('websockets.connect', return_value=mock_websocket):
        conn = WebSocketConnection("stocks", "wss://test.com", "test_key")
        await conn.connect()

        assert conn.state == ConnectionState.CONNECTED
        mock_websocket.send.assert_called_once()


@pytest.mark.asyncio
async def test_authentication_failure(mock_websocket):
    """Test authentication failure handling."""
    # Mock auth failed response
    mock_websocket.recv.return_value = '[{"ev":"status","status":"auth_failed","message":"Invalid key"}]'

    with patch('websockets.connect', return_value=mock_websocket):
        conn = WebSocketConnection("stocks", "wss://test.com", "bad_key")

        with pytest.raises(Exception, match="Authentication failed"):
            await conn.connect()


@pytest.mark.asyncio
async def test_subscribe_channels(mock_websocket):
    """Test subscribing to channels."""
    mock_websocket.recv.return_value = '[{"ev":"status","status":"auth_success"}]'

    with patch('websockets.connect', return_value=mock_websocket):
        conn = WebSocketConnection("stocks", "wss://test.com", "test_key")
        await conn.connect()

        await conn.subscribe(["T.AAPL", "Q.MSFT"])

        assert "T.AAPL" in conn.subscriptions
        assert "Q.MSFT" in conn.subscriptions
        assert len(conn.subscriptions) == 2


@pytest.mark.asyncio
async def test_reconnection_backoff():
    """Test exponential backoff on reconnection."""
    conn = WebSocketConnection("stocks", "wss://test.com", "test_key")

    # Test backoff delays
    assert conn.reconnect_attempts == 0
    conn.reconnect_attempts = 3
    delay = min(2 ** conn.reconnect_attempts, conn.max_reconnect_delay)
    assert delay == 8  # 2^3 = 8 seconds


# Additional 20 tests for:
# - Unsubscribe channels
# - Resubscription after reconnect
# - Message routing
# - Error handling
# - Connection state transitions
# - Multiple connections via ConnectionManager
# - etc.
```

`test_stream_formatter.py` (20 tests):
```python
"""
Tests for stream message formatting.

Verifies JSON formatting for all message types.
"""

import json
import pytest
from src.mcp_polygon.tools.websockets.stream_formatter import (
    format_stream_message,
    format_status_message,
    _format_trade,
    _format_quote,
    _format_aggregate
)


def test_format_trade_message():
    """Test trade message formatting."""
    trade = {
        "ev": "T",
        "sym": "AAPL",
        "p": 150.25,
        "s": 100,
        "x": 4,
        "c": [0, 12],
        "t": 1640995200000
    }

    result = format_stream_message(trade, pretty=False)
    data = json.loads(result)

    assert data["event"] == "TRADE"
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.25
    assert data["size"] == 100


def test_format_quote_message():
    """Test quote message formatting."""
    quote = {
        "ev": "Q",
        "sym": "MSFT",
        "bp": 300.50,
        "ap": 300.52,
        "bs": 100,
        "as": 50,
        "bx": 11,
        "ax": 11,
        "t": 1640995200000
    }

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["event"] == "QUOTE"
    assert data["symbol"] == "MSFT"
    assert data["bid"]["price"] == 300.50
    assert data["ask"]["price"] == 300.52
    assert data["spread"] == 0.02


def test_format_aggregate_minute():
    """Test minute aggregate formatting."""
    agg = {
        "ev": "AM",
        "sym": "TSLA",
        "o": 200.0,
        "h": 202.5,
        "l": 199.5,
        "c": 201.0,
        "v": 50000,
        "av": 1000000,
        "vw": 200.75,
        "s": 1640995200000,
        "e": 1640995260000
    }

    result = format_stream_message(agg, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_MINUTE"
    assert data["symbol"] == "TSLA"
    assert data["open"] == 200.0
    assert data["close"] == 201.0


# Additional 17 tests for:
# - Second aggregates
# - Index values
# - LULD messages
# - FMV messages
# - Status messages
# - Error cases
# - Timestamp conversion
# - etc.
```

**Integration Tests (Delayed Endpoint):**

`test_integration_ws.py` (10 tests):
```python
"""
Integration tests using delayed WebSocket endpoint.

Uses real connections to delayed.polygon.io (no API key required for testing).
"""

import pytest
import asyncio
from src.mcp_polygon.tools.websockets.connection_manager import ConnectionManager


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delayed_connection():
    """Test connection to delayed endpoint."""
    manager = ConnectionManager()

    conn = manager.get_connection(
        "stocks",
        endpoint="wss://delayed.polygon.io/stocks",
        api_key="test"  # Delayed endpoint accepts any key
    )

    await conn.connect()
    assert conn.state.value == "connected"
    await conn.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscription_flow():
    """Test full subscribe → receive data → unsubscribe flow."""
    manager = ConnectionManager()

    conn = manager.get_connection(
        "stocks",
        endpoint="wss://delayed.polygon.io/stocks",
        api_key="test"
    )

    await conn.connect()

    # Subscribe to high-volume ticker
    await conn.subscribe(["T.AAPL"])

    # Wait for at least one message (timeout 30s)
    received = []

    async def handler(msg):
        received.append(msg)

    conn.add_message_handler(handler)

    await asyncio.sleep(30)

    assert len(received) > 0, "Should receive at least one message"

    await conn.unsubscribe(["T.AAPL"])
    await conn.close()


# Additional 8 integration tests for:
# - Multiple concurrent connections
# - Reconnection after disconnect
# - Message volume handling
# - Error recovery
# - etc.
```

### 4.3 Coverage Goals

| Component | Target Coverage | Tests |
|-----------|----------------|-------|
| Connection Manager | 100% | 25 |
| Stream Formatter | 100% | 20 |
| Stocks Tools | 90% | 15 |
| Options Tools | 90% | 10 |
| Futures Tools | 90% | 10 |
| Indices Tools | 90% | 10 |
| Forex Tools | 90% | 10 |
| Crypto Tools | 90% | 10 |
| Integration | 80% | 10 |

**Total:** 120 new tests

### 4.4 Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run only WebSocket tests
pytest tests/test_websockets/ -v

# Run unit tests (fast)
pytest tests/test_websockets/ -v -m "not integration"

# Run integration tests (slow, uses live API)
pytest tests/test_websockets/ -v -m integration

# Coverage report
pytest tests/test_websockets/ --cov=src/mcp_polygon/tools/websockets --cov-report=html

# Specific market tests
pytest tests/test_websockets/test_stocks_ws.py -v
```

### 4.5 Manual Testing Checklist

**Using MCP Inspector:**

1. **Connection Lifecycle:**
   - [ ] Start stream connects successfully
   - [ ] Authentication succeeds
   - [ ] Stop stream closes connection
   - [ ] Status shows correct state

2. **Subscriptions:**
   - [ ] Subscribe adds channels
   - [ ] Unsubscribe removes channels
   - [ ] List shows all active channels
   - [ ] Wildcard subscriptions work

3. **Data Reception:**
   - [ ] Trade messages format correctly
   - [ ] Quote messages format correctly
   - [ ] Aggregate messages format correctly
   - [ ] Timestamps are readable

4. **Error Handling:**
   - [ ] Invalid API key shows clear error
   - [ ] Invalid channels show clear error
   - [ ] Connection loss triggers reconnect
   - [ ] Subscription to closed connection fails gracefully

5. **Multi-Market:**
   - [ ] Can run stocks + crypto simultaneously
   - [ ] Each market maintains separate subscriptions
   - [ ] Stopping one market doesn't affect others

---

## Phase 5: Documentation & Polish (Weeks 11-12)

### 5.1 Documentation Updates

**CLAUDE.md Updates:**

Add WebSocket section after REST tools section:

```markdown
## WebSocket Tools (Real-Time Streaming)

The server provides WebSocket streaming tools for real-time market data across 6 asset classes.

### Architecture

WebSocket tools are fundamentally different from REST tools:
- **REST:** Request → Response (stateless, milliseconds)
- **WebSocket:** Connection → Stream (stateful, continuous)

### Tool Categories

**Connection Tools** (start/stop/status):
- `start_{market}_stream(channels, api_key, endpoint)` → Begin streaming
- `stop_{market}_stream()` → End streaming
- `get_{market}_stream_status()` → Check connection state

**Subscription Tools** (subscribe/unsubscribe/list):
- `subscribe_{market}_channels(channels)` → Add channels to stream
- `unsubscribe_{market}_channels(channels)` → Remove channels
- `list_{market}_subscriptions()` → Show active subscriptions

### Markets

| Market | Channels | Trading Hours | Documentation |
|--------|----------|---------------|---------------|
| Stocks | T, Q, AM, A, LULD, FMV | 9:30 AM-4:00 PM ET + extended | [stocks/overview.md](polygon-docs/websockets/stocks/overview.md) |
| Options | T.O:, Q.O:, AM.O:, AS.O:, FMV.O: | 9:30 AM-4:00 PM ET | [options/overview.md](polygon-docs/websockets/options/overview.md) |
| Futures | T, Q, AM, AS | ~24/5 (varies) | [futures/overview.md](polygon-docs/websockets/futures/overview.md) |
| Indices | V.I:, AM.I:, AS.I: | 9:30 AM-4:00 PM ET | [indices/overview.md](polygon-docs/websockets/indices/overview.md) |
| Forex | C, CA, CAS, FMV | 24/5 | [forex/overview.md](polygon-docs/websockets/forex/overview.md) |
| Crypto | XT, XQ, XA, XAS, FMV | 24/7 | [crypto/overview.md](polygon-docs/websockets/crypto/overview.md) |

### Example Usage

Start streaming Apple stock trades and quotes:
```
start_stocks_stream(channels=["T.AAPL", "Q.AAPL"])
```

Add minute aggregates to existing stream:
```
subscribe_stocks_channels(channels=["AM.AAPL"])
```

Check connection status:
```
get_stocks_stream_status()
```

Stop streaming:
```
stop_stocks_stream()
```

### Data Format

WebSocket tools return JSON (not CSV) because:
1. Real-time data needs timestamps and metadata
2. JSON preserves data types (floats, ints, booleans)
3. Nested structures (conditions, Greeks) require JSON
4. LLMs handle streaming JSON efficiently

### Adding WebSocket Tools

See [WebSocket Implementation Guide](WEBSOCKETS_IMPLEMENTATION.md) for:
- Connection management patterns
- Documentation cross-reference requirements
- Testing procedures
```

**New Documentation File: WEBSOCKETS.md**

Create comprehensive user guide:

```markdown
# WebSocket Streaming Guide - MCP Polygon Server

## Overview

The MCP Polygon server provides real-time WebSocket streaming for 6 asset classes:
stocks, options, futures, indices, forex, and crypto.

## Quick Start

### 1. Start a Stream

```
start_stocks_stream(
    channels=["T.AAPL", "Q.AAPL", "AM.AAPL"],
    endpoint="wss://socket.polygon.io/stocks"
)
```

### 2. Receive Data

Data streams continuously as JSON messages:
```json
{
  "event": "TRADE",
  "symbol": "AAPL",
  "price": 150.25,
  "size": 100,
  "timestamp": "2024-01-01T14:30:00",
  "full_data": {...}
}
```

### 3. Stop Stream

```
stop_stocks_stream()
```

## Channel Reference

[Complete channel reference with examples for each market...]

## Common Use Cases

[Examples for dashboards, alerts, analysis, etc...]

## Troubleshooting

[Common issues and solutions...]
```

**Update README.md:**

Add WebSocket features to main README:

```markdown
## Features

### REST API (81 tools)
- Historical market data across 7 asset classes
- CSV-formatted responses for token efficiency
- 99% Polygon API endpoint coverage

### WebSocket Streaming (36 tools)
- Real-time market data streams
- 6 asset classes (stocks, options, futures, indices, forex, crypto)
- Connection management with auto-reconnect
- Subscription control (add/remove channels dynamically)
- JSON-formatted streaming data

[...]
```

### 5.2 Code Quality Checklist

**Pre-Release:**

1. **Linting:**
```bash
just lint  # ruff format + check
```

2. **Testing:**
```bash
pytest tests/ -v --cov=src/mcp_polygon --cov-report=html
# Target: 90%+ overall coverage
```

3. **Security Review:**
- [ ] API keys not logged
- [ ] WebSocket connections properly closed
- [ ] No memory leaks in long-running streams
- [ ] Error messages don't expose sensitive info
- [ ] Rate limiting respected

4. **Performance Testing:**
```python
# Test connection limits
# Start 10 concurrent streams
for market in markets:
    start_{market}_stream(...)

# Monitor memory usage over 1 hour
# Verify no memory leaks

# Test message throughput
# Subscribe to T.* (all tickers)
# Measure messages/second
# Verify no dropped messages
```

5. **Error Message Quality:**
- [ ] All errors are LLM-friendly (clear, actionable)
- [ ] No technical jargon without explanation
- [ ] Suggest next steps in error messages
- [ ] Include documentation references

6. **Documentation Review:**
- [ ] All doc cross-references are valid
- [ ] Examples work as written
- [ ] API tier requirements clearly stated
- [ ] Troubleshooting covers common issues

---

## Implementation Timeline

| Phase | Duration | Key Deliverables | Success Criteria |
|-------|----------|------------------|------------------|
| **Phase 1: Reorganization** | Weeks 1-2 | • Directory restructure<br>• Updated imports<br>• All tests passing | • 81 REST tools working<br>• Zero regression<br>• Tests pass |
| **Phase 2: Infrastructure** | Weeks 3-4 | • ConnectionManager<br>• StreamFormatter<br>• Core utilities | • Unit tests pass<br>• Code review approved |
| **Phase 3: Tools** | Weeks 5-8 | • 36 WebSocket tools<br>• 6 markets implemented<br>• Doc cross-refs | • All tools work<br>• 90%+ test coverage<br>• MCP Inspector validated |
| **Phase 4: Testing** | Weeks 9-10 | • 120 new tests<br>• Integration tests<br>• Live API validation | • 90%+ coverage<br>• All tests pass<br>• Performance validated |
| **Phase 5: Polish** | Weeks 11-12 | • Documentation<br>• Code review<br>• Security audit | • Docs complete<br>• Security 8/10+<br>• Production ready |

**Total Duration:** 12 weeks

**Milestones:**
- **Week 2:** Server reorganized, REST tools still working
- **Week 4:** WebSocket infrastructure complete
- **Week 6:** 50% of WebSocket tools implemented (stocks, crypto, options)
- **Week 8:** 100% of WebSocket tools implemented
- **Week 10:** Testing complete, all tests passing
- **Week 12:** Production ready, documentation complete

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **WebSocket connection instability** | High | Medium | • Implement robust reconnection<br>• Exponential backoff<br>• Connection health monitoring |
| **State management complexity** | Medium | Medium | • Clear lifecycle (start → stream → stop)<br>• ConnectionManager singleton<br>• Extensive unit tests |
| **Message volume performance** | Medium | Low | • Rate limiting<br>• Backpressure handling<br>• Subscription filtering |
| **MCP protocol limitations** | High | Low | • Early research into MCP streaming<br>• Consider SSE transport fallback |

### Compatibility Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Breaking REST API changes** | Critical | Very Low | • Extensive testing in Phase 1<br>• Keep REST interfaces unchanged<br>• Backward compatibility tests |
| **Python version compatibility** | Medium | Low | • Test on Python 3.9-3.12<br>• Pin dependencies |
| **WebSocket library issues** | Medium | Low | • Use battle-tested `websockets` library<br>• Pin version |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Timeline delays** | Medium | Medium | • Buffer weeks in Phase 5<br>• Parallel tool implementation<br>• Regular progress reviews |
| **API tier limitations** | Low | Medium | • Clear docs on tier requirements<br>• Test with delayed endpoints<br>• Graceful degradation |
| **Documentation drift** | Low | Medium | • Doc cross-refs in code<br>• Regular doc reviews<br>• CI validation of links |

---

## Success Criteria

### Functional Requirements

| Requirement | Success Metric |
|-------------|---------------|
| All 6 markets have streaming | ✅ 36 tools implemented (6 per market) |
| Connection lifecycle works | ✅ Start → stream → stop works reliably |
| Subscription management works | ✅ Add/remove channels dynamically |
| Error handling is helpful | ✅ All errors have clear messages + docs |
| Auto-reconnection works | ✅ Reconnects within 30s of disconnect |
| REST tools unchanged | ✅ Zero regression in existing tools |

### Quality Requirements

| Requirement | Success Metric |
|-------------|---------------|
| Test coverage | ✅ ≥90% for WebSocket code |
| Code quality | ✅ Score A- or better (88+/100) |
| Security review | ✅ Score 8/10 or better |
| Documentation complete | ✅ All files updated, examples work |
| Linting passes | ✅ `just lint` with zero errors |

### Performance Requirements

| Requirement | Success Metric |
|-------------|---------------|
| Concurrent connections | ✅ Support ≥5 simultaneous streams |
| Message throughput | ✅ Handle ≥1000 messages/second/connection |
| Memory stability | ✅ No leaks over 24-hour test |
| Reconnection speed | ✅ Reconnect within 5 seconds |
| Latency | ✅ Message delivery < 100ms from market event |

### User Experience Requirements

| Requirement | Success Metric |
|-------------|---------------|
| Easy to start streaming | ✅ 1 command to start stream |
| Clear status visibility | ✅ Status command shows all info |
| Helpful error messages | ✅ 100% of errors suggest next steps |
| Complete documentation | ✅ All use cases covered with examples |
| MCP Inspector works | ✅ All tools discoverable and testable |

---

## Appendix: Tool Inventory

### WebSocket Tools by Market

**Stocks** (6 tools):
1. `start_stocks_stream(channels, api_key, endpoint)`
2. `stop_stocks_stream()`
3. `get_stocks_stream_status()`
4. `subscribe_stocks_channels(channels)`
5. `unsubscribe_stocks_channels(channels)`
6. `list_stocks_subscriptions()`

**Options** (6 tools):
1. `start_options_stream(channels, api_key, endpoint)`
2. `stop_options_stream()`
3. `get_options_stream_status()`
4. `subscribe_options_channels(channels)`
5. `unsubscribe_options_channels(channels)`
6. `list_options_subscriptions()`

**Futures** (6 tools):
1. `start_futures_stream(channels, api_key, endpoint)`
2. `stop_futures_stream()`
3. `get_futures_stream_status()`
4. `subscribe_futures_channels(channels)`
5. `unsubscribe_futures_channels(channels)`
6. `list_futures_subscriptions()`

**Indices** (6 tools):
1. `start_indices_stream(channels, api_key, endpoint)`
2. `stop_indices_stream()`
3. `get_indices_stream_status()`
4. `subscribe_indices_channels(channels)`
5. `unsubscribe_indices_channels(channels)`
6. `list_indices_subscriptions()`

**Forex** (6 tools):
1. `start_forex_stream(channels, api_key, endpoint)`
2. `stop_forex_stream()`
3. `get_forex_stream_status()`
4. `subscribe_forex_channels(channels)`
5. `unsubscribe_forex_channels(channels)`
6. `list_forex_subscriptions()`

**Crypto** (6 tools):
1. `start_crypto_stream(channels, api_key, endpoint)`
2. `stop_crypto_stream()`
3. `get_crypto_stream_status()`
4. `subscribe_crypto_channels(channels)`
5. `unsubscribe_crypto_channels(channels)`
6. `list_crypto_subscriptions()`

**Total:** 36 WebSocket tools

**Combined with REST:** 81 + 36 = **117 total tools**

---

## Next Steps

**Before Starting Implementation:**

1. **Review & Approval:**
   - [ ] Review this plan
   - [ ] Approve 12-week timeline
   - [ ] Approve tool architecture (36 tools)
   - [ ] Approve JSON format for streaming
   - [ ] Approve doc cross-reference requirement

2. **Project Setup:**
   - [ ] Create GitHub milestone "WebSocket Implementation"
   - [ ] Create branch `websockets-implementation`
   - [ ] Set up project board with tasks
   - [ ] Assign team members (if applicable)

3. **Environment Setup:**
   - [ ] Install WebSocket library: `pip install websockets`
   - [ ] Test delayed endpoint access
   - [ ] Verify API key has WebSocket access

**First Implementation Task:**

Execute **Phase 1.1: Directory Structure Migration**

Commands:
```bash
git checkout -b websockets-implementation
mkdir -p src/mcp_polygon/tools/rest
mkdir -p src/mcp_polygon/tools/websockets
# Follow Phase 1.2 migration steps...
```

---

## Questions for Review

1. **JSON Format:** Approve JSON (not CSV) for WebSocket messages?
2. **Tool Count:** Approve ~36 WebSocket tools (6 tools × 6 markets)?
3. **Timeline:** Approve 12-week implementation timeline?
4. **Documentation:** Approve mandatory doc cross-references in tool comments?
5. **Testing:** Approve 120 new tests target?
6. **Markets:** Any additional markets/channels to prioritize?

---

**End of Implementation Plan**

**Document Version:** 1.0
**Last Updated:** 2025-10-17
**Status:** Ready for Review
