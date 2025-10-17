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
import ssl
from typing import Dict, List, Optional, Callable, Set
from enum import Enum
from collections import deque
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class APIAccessError(Exception):
    """Raised when API plan doesn't include requested data access."""
    pass


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
        self._receive_task: Optional[asyncio.Task] = None
        self.message_buffer: deque = deque(maxlen=100)  # Circular buffer for recent messages
        self._total_messages_received: int = 0  # Lifetime counter
        self.last_error: Optional[str] = None  # Store last API access error

    async def connect(self) -> None:
        """
        Establish WebSocket connection and authenticate.

        Documentation: polygon-docs/websockets/quickstart.md:65-92
        """
        try:
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to {self.endpoint}")

            # Create SSL context with system certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            self.websocket = await websockets.connect(
                self.endpoint,
                ping_interval=30,
                ping_timeout=10,
                ssl=ssl_context
            )

            self.state = ConnectionState.AUTHENTICATING
            await self._authenticate()

            # Set CONNECTED state before starting tasks/resubscribing
            self.reconnect_attempts = 0
            self.state = ConnectionState.CONNECTED

            # Cancel old receive task if exists (prevents ConcurrencyError)
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass

            # Start new message receiver task
            self._receive_task = asyncio.create_task(self._receive_messages())

            # Resubscribe to previous channels if reconnecting
            if self.subscriptions:
                await self._resubscribe()

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
                            try:
                                self._handle_status(msg)
                            except APIAccessError as e:
                                # Store error for status queries
                                self.last_error = str(e)
                                self.state = ConnectionState.ERROR
                                logger.error(f"⚠️  API Access Error: {e}")
                                # Don't raise - keep connection alive for potential delayed endpoint reconnect
                                continue
                        else:
                            # Buffer data messages (status messages are NOT buffered)
                            self.message_buffer.append(msg)
                            self._total_messages_received += 1

                            # Route market data to handlers
                            for handler in self.message_handlers:
                                await handler(msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {message}, error: {e}")

        except ConnectionClosed as e:
            logger.warning(f"Connection closed: {e}")
            await self._handle_connection_error(e)
        except asyncio.CancelledError:
            logger.info("Receive task cancelled (connection closing)")
            raise  # Re-raise to properly cancel task

    def _handle_status(self, status_msg: dict) -> None:
        """Handle WebSocket status messages."""
        status = status_msg.get("status")
        message = status_msg.get("message", "")

        # Trap API plan access errors for user-friendly messaging
        if status == "error" and "don't have access" in message:
            raise APIAccessError(
                f"API Plan Limitation: {message}\n\n"
                f"Your plan includes 15-minute delayed data. To access real-time data:\n"
                f"1. Upgrade at https://polygon.io/pricing\n"
                f"2. Or use delayed endpoint: wss://delayed.polygon.io/{self.market}\n\n"
                f"Note: Delayed endpoint is automatically used based on your API key."
            )

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
        # Clear buffer on disconnect
        self.clear_message_buffer()

        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()
            self.state = ConnectionState.DISCONNECTED
            logger.info(f"✓ Closed {self.market} WebSocket")

    def add_message_handler(self, handler: Callable) -> None:
        """Add a message handler callback."""
        self.message_handlers.append(handler)

    def get_status(self) -> dict:
        """Get connection status."""
        status = {
            "market": self.market,
            "state": self.state.value,
            "endpoint": self.endpoint,
            "subscriptions": list(self.subscriptions),
            "subscription_count": len(self.subscriptions),
        }
        if self.last_error:
            status["last_error"] = self.last_error
        return status

    def get_recent_messages(self, limit: int = 10) -> List[dict]:
        """
        Get N most recent messages from buffer.

        Args:
            limit: Number of messages to retrieve (default: 10, max: buffer size)

        Returns:
            List of message dicts in chronological order (oldest first)
        """
        limit = min(limit, len(self.message_buffer))
        return list(self.message_buffer)[-limit:] if limit > 0 else []

    def get_message_stats(self) -> dict:
        """
        Get message reception statistics.

        Returns:
            Dict with keys: total_received, buffered, buffer_capacity
        """
        return {
            "total_received": self._total_messages_received,
            "buffered": len(self.message_buffer),
            "buffer_capacity": self.message_buffer.maxlen,
        }

    def clear_message_buffer(self) -> None:
        """Clear message buffer (called on disconnect)."""
        self.message_buffer.clear()


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
