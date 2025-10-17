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
                self.endpoint, ping_interval=30, ping_timeout=10
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
        auth_message = {"action": "auth", "params": self.api_key}
        await self.websocket.send(json.dumps(auth_message))
        logger.debug("→ Authentication message sent")

        # Wait for auth success - may receive multiple messages
        # First message might be connection status, then auth response
        max_attempts = 5
        for attempt in range(max_attempts):
            response = await self.websocket.recv()
            messages = json.loads(response)

            for msg in messages:
                if msg.get("ev") == "status":
                    status = msg.get("status")
                    if status == "auth_success":
                        logger.info("✓ Authentication successful")
                        return
                    elif status == "auth_failed":
                        raise Exception(f"Authentication failed: {msg.get('message')}")
                    elif status == "connected":
                        logger.debug("Received connection status, waiting for auth response")
                        continue

        raise Exception("No authentication response received after multiple attempts")

    async def subscribe(self, channels: List[str]) -> None:
        """
        Subscribe to data channels.

        Args:
            channels: List of channel subscriptions (e.g., ["T.AAPL", "Q.MSFT"])

        Documentation: polygon-docs/websockets/quickstart.md:245-278
        """
        if self.state != ConnectionState.CONNECTED:
            raise Exception(f"Cannot subscribe: connection state is {self.state.value}")

        subscribe_message = {"action": "subscribe", "params": ",".join(channels)}
        await self.websocket.send(json.dumps(subscribe_message))

        self.subscriptions.update(channels)
        logger.info(f"→ Subscribed to {len(channels)} channels")

    async def unsubscribe(self, channels: List[str]) -> None:
        """
        Unsubscribe from data channels.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119
        """
        if self.state != ConnectionState.CONNECTED:
            raise Exception(
                f"Cannot unsubscribe: connection state is {self.state.value}"
            )

        unsubscribe_message = {"action": "unsubscribe", "params": ",".join(channels)}
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
        delay = min(2**self.reconnect_attempts, self.max_reconnect_delay)
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
            "subscription_count": len(self.subscriptions),
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
        self, market: str, endpoint: Optional[str] = None, api_key: Optional[str] = None
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
