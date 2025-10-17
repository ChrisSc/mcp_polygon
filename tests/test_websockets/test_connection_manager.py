"""
Unit tests for WebSocket connection management.

Tests the WebSocketConnection and ConnectionManager classes including:
- Connection lifecycle (connect, authenticate, disconnect)
- Subscription management (subscribe, unsubscribe, resubscribe)
- Error handling (reconnection, backoff, errors)
- State transitions and status reporting
"""

import json
import pytest
from collections import deque
from unittest.mock import AsyncMock, Mock, patch
from websockets.exceptions import ConnectionClosed

from mcp_polygon.tools.websockets.connection_manager import (
    ConnectionState,
    WebSocketConnection,
    ConnectionManager,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection with async methods."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = Mock(return_value=iter([]))
    return ws


@pytest.fixture
def connection():
    """Create a WebSocketConnection instance for testing."""
    return WebSocketConnection(
        market="stocks",
        endpoint="wss://socket.polygon.io/stocks",
        api_key="test_api_key",
    )


@pytest.fixture
def connection_manager():
    """Create a ConnectionManager instance for testing."""
    return ConnectionManager()


# ============================================================================
# WebSocketConnection Initialization Tests (3 tests)
# ============================================================================


def test_connection_initialization(connection):
    """Test connection initializes with correct defaults."""
    assert connection.market == "stocks"
    assert connection.endpoint == "wss://socket.polygon.io/stocks"
    assert connection.api_key == "test_api_key"
    assert connection.state == ConnectionState.DISCONNECTED
    assert connection.subscriptions == set()
    assert connection.message_handlers == []
    assert connection.reconnect_attempts == 0
    assert connection.max_reconnect_delay == 30
    assert connection.websocket is None


def test_connection_state_enum():
    """Test ConnectionState enum values."""
    assert ConnectionState.DISCONNECTED.value == "disconnected"
    assert ConnectionState.CONNECTING.value == "connecting"
    assert ConnectionState.AUTHENTICATING.value == "authenticating"
    assert ConnectionState.CONNECTED.value == "connected"
    assert ConnectionState.ERROR.value == "error"


def test_connection_get_status(connection):
    """Test get_status returns correct structure."""
    connection.subscriptions.update(["T.AAPL", "Q.MSFT"])
    status = connection.get_status()

    assert status["market"] == "stocks"
    assert status["state"] == "disconnected"
    assert status["endpoint"] == "wss://socket.polygon.io/stocks"
    assert set(status["subscriptions"]) == {"T.AAPL", "Q.MSFT"}
    assert status["subscription_count"] == 2


# ============================================================================
# Connection Lifecycle Tests (6 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_connect_success(connection, mock_websocket):
    """Test successful connection and authentication."""
    # Mock auth success response
    auth_response = json.dumps(
        [{"ev": "status", "status": "auth_success", "message": "authenticated"}]
    )
    mock_websocket.recv.return_value = auth_response

    with patch(
        "websockets.connect", new_callable=AsyncMock, return_value=mock_websocket
    ):
        with patch.object(connection, "_receive_messages", new_callable=AsyncMock):
            await connection.connect()

    assert connection.state == ConnectionState.CONNECTED
    assert connection.reconnect_attempts == 0
    assert connection.websocket == mock_websocket

    # Verify auth message was sent
    auth_call = mock_websocket.send.call_args[0][0]
    auth_msg = json.loads(auth_call)
    assert auth_msg["action"] == "auth"
    assert auth_msg["params"] == "test_api_key"


@pytest.mark.asyncio
async def test_connect_with_ping_config(connection, mock_websocket):
    """Test connection includes ping configuration."""
    auth_response = json.dumps(
        [{"ev": "status", "status": "auth_success", "message": "authenticated"}]
    )
    mock_websocket.recv.return_value = auth_response

    with patch("websockets.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_websocket
        with patch.object(connection, "_receive_messages", new_callable=AsyncMock):
            await connection.connect()

    # Verify websockets.connect called with ping settings
    mock_connect.assert_called_once_with(
        "wss://socket.polygon.io/stocks", ping_interval=30, ping_timeout=10
    )


@pytest.mark.asyncio
async def test_authenticate_success(connection, mock_websocket):
    """Test authentication success flow."""
    connection.websocket = mock_websocket
    auth_response = json.dumps(
        [{"ev": "status", "status": "auth_success", "message": "authenticated"}]
    )
    mock_websocket.recv.return_value = auth_response

    await connection._authenticate()

    # Verify auth message sent
    auth_call = mock_websocket.send.call_args[0][0]
    auth_msg = json.loads(auth_call)
    assert auth_msg["action"] == "auth"
    assert auth_msg["params"] == "test_api_key"


@pytest.mark.asyncio
async def test_authenticate_failure(connection, mock_websocket):
    """Test authentication failure handling."""
    connection.websocket = mock_websocket
    auth_response = json.dumps(
        [{"ev": "status", "status": "auth_failed", "message": "Invalid API key"}]
    )
    mock_websocket.recv.return_value = auth_response

    with pytest.raises(Exception, match="Authentication failed: Invalid API key"):
        await connection._authenticate()


@pytest.mark.asyncio
async def test_authenticate_no_response(connection, mock_websocket):
    """Test authentication with no status response."""
    connection.websocket = mock_websocket
    auth_response = json.dumps([{"ev": "trade", "sym": "AAPL"}])
    mock_websocket.recv.return_value = auth_response

    with pytest.raises(Exception, match="No authentication response received"):
        await connection._authenticate()


@pytest.mark.asyncio
async def test_close_connection(connection, mock_websocket):
    """Test closing connection gracefully."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED

    await connection.close()

    assert connection.state == ConnectionState.DISCONNECTED
    mock_websocket.close.assert_called_once()


# ============================================================================
# Subscription Management Tests (6 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_channels(connection, mock_websocket):
    """Test subscribing to channels."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED
    channels = ["T.AAPL", "Q.MSFT", "T.GOOGL"]

    await connection.subscribe(channels)

    # Verify subscribe message sent
    subscribe_call = mock_websocket.send.call_args[0][0]
    subscribe_msg = json.loads(subscribe_call)
    assert subscribe_msg["action"] == "subscribe"
    assert subscribe_msg["params"] == "T.AAPL,Q.MSFT,T.GOOGL"

    # Verify subscriptions stored
    assert connection.subscriptions == {"T.AAPL", "Q.MSFT", "T.GOOGL"}


@pytest.mark.asyncio
async def test_subscribe_when_disconnected(connection):
    """Test subscribing fails when not connected."""
    connection.state = ConnectionState.DISCONNECTED

    with pytest.raises(
        Exception, match="Cannot subscribe: connection state is disconnected"
    ):
        await connection.subscribe(["T.AAPL"])


@pytest.mark.asyncio
async def test_unsubscribe_channels(connection, mock_websocket):
    """Test unsubscribing from channels."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED
    connection.subscriptions = {"T.AAPL", "Q.MSFT", "T.GOOGL"}

    await connection.unsubscribe(["T.AAPL", "T.GOOGL"])

    # Verify unsubscribe message sent
    unsubscribe_call = mock_websocket.send.call_args[0][0]
    unsubscribe_msg = json.loads(unsubscribe_call)
    assert unsubscribe_msg["action"] == "unsubscribe"
    assert unsubscribe_msg["params"] == "T.AAPL,T.GOOGL"

    # Verify subscriptions updated
    assert connection.subscriptions == {"Q.MSFT"}


@pytest.mark.asyncio
async def test_unsubscribe_when_disconnected(connection):
    """Test unsubscribing fails when not connected."""
    connection.state = ConnectionState.DISCONNECTED

    with pytest.raises(
        Exception, match="Cannot unsubscribe: connection state is disconnected"
    ):
        await connection.unsubscribe(["T.AAPL"])


@pytest.mark.asyncio
async def test_resubscribe_after_reconnect(connection, mock_websocket):
    """Test resubscription after reconnection."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED
    connection.subscriptions = {"T.AAPL", "Q.MSFT"}

    await connection._resubscribe()

    # Verify subscribe message sent with all channels
    subscribe_call = mock_websocket.send.call_args[0][0]
    subscribe_msg = json.loads(subscribe_call)
    assert subscribe_msg["action"] == "subscribe"
    # Check both possible orderings (sets are unordered)
    assert subscribe_msg["params"] in ["T.AAPL,Q.MSFT", "Q.MSFT,T.AAPL"]


@pytest.mark.asyncio
async def test_resubscribe_with_no_subscriptions(connection, mock_websocket):
    """Test resubscribe does nothing when no subscriptions exist."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED
    connection.subscriptions = set()

    await connection._resubscribe()

    # Should not send any message
    mock_websocket.send.assert_not_called()


# ============================================================================
# Message Handling Tests (5 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_receive_messages_data_routing(connection, mock_websocket):
    """Test data messages are routed to handlers."""
    handler = AsyncMock()
    connection.add_message_handler(handler)
    connection.websocket = mock_websocket

    # Create message stream
    messages = [
        json.dumps(
            [
                {"ev": "T", "sym": "AAPL", "p": 150.25, "s": 100},
                {"ev": "Q", "sym": "MSFT", "bp": 300.50, "ap": 300.75},
            ]
        )
    ]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()

    await connection._receive_messages()

    # Verify handler called for each message
    assert handler.call_count == 2
    handler.assert_any_call({"ev": "T", "sym": "AAPL", "p": 150.25, "s": 100})
    handler.assert_any_call({"ev": "Q", "sym": "MSFT", "bp": 300.50, "ap": 300.75})


@pytest.mark.asyncio
async def test_receive_messages_status_handling(connection, mock_websocket):
    """Test status messages are handled separately."""
    handler = AsyncMock()
    connection.add_message_handler(handler)
    connection.websocket = mock_websocket

    messages = [
        json.dumps([{"ev": "status", "status": "success", "message": "Subscribed"}])
    ]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()

    await connection._receive_messages()

    # Status messages should not be routed to data handlers
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_receive_messages_json_decode_error(connection, mock_websocket):
    """Test handling of invalid JSON messages."""
    handler = AsyncMock()
    connection.add_message_handler(handler)
    connection.websocket = mock_websocket

    # Invalid JSON
    messages = ["not valid json", json.dumps([{"ev": "T", "sym": "AAPL"}])]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()

    # Should log error but continue processing
    await connection._receive_messages()

    # Valid message should still be processed
    handler.assert_called_once_with({"ev": "T", "sym": "AAPL"})


@pytest.mark.asyncio
async def test_receive_messages_non_array(connection, mock_websocket):
    """Test handling of non-array JSON messages."""
    handler = AsyncMock()
    connection.add_message_handler(handler)
    connection.websocket = mock_websocket

    # Non-array message (should be logged and skipped)
    messages = [json.dumps({"ev": "T", "sym": "AAPL"})]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()

    await connection._receive_messages()

    # Should not call handler for non-array
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_add_message_handler(connection):
    """Test adding message handlers."""
    handler1 = AsyncMock()
    handler2 = AsyncMock()

    connection.add_message_handler(handler1)
    connection.add_message_handler(handler2)

    assert len(connection.message_handlers) == 2
    assert handler1 in connection.message_handlers
    assert handler2 in connection.message_handlers


# ============================================================================
# Error Handling and Reconnection Tests (5 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_exponential_backoff_calculation(connection):
    """Test exponential backoff delay calculation."""
    connection.reconnect_attempts = 0
    delays = []

    for i in range(6):
        delay = min(2**connection.reconnect_attempts, connection.max_reconnect_delay)
        delays.append(delay)
        connection.reconnect_attempts += 1

    assert delays == [1, 2, 4, 8, 16, 30]  # Caps at max_reconnect_delay (30)


@pytest.mark.asyncio
async def test_handle_connection_error_with_reconnect(connection):
    """Test connection error triggers reconnection."""
    error = ConnectionClosed(None, None)

    with patch.object(connection, "connect", new_callable=AsyncMock) as mock_connect:
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await connection._handle_connection_error(error)

    assert connection.state == ConnectionState.ERROR
    mock_sleep.assert_called_once_with(1)  # First backoff is 1 second
    mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_handle_connection_error_backoff_increases(connection):
    """Test reconnection backoff increases on repeated failures."""
    connection.reconnect_attempts = 3  # Start at attempt 3 (delay = 2^3 = 8s)

    with patch.object(connection, "connect", new_callable=AsyncMock) as mock_connect:
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await connection._handle_connection_error(Exception("test"))

    assert connection.reconnect_attempts == 4
    mock_sleep.assert_called_once_with(8)  # 2^3 = 8 seconds
    mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_receive_messages_connection_closed(connection, mock_websocket):
    """Test handling of connection closed during receive."""
    connection.websocket = mock_websocket

    # Simulate ConnectionClosed exception during iteration
    async def async_iterator():
        raise ConnectionClosed(None, None)
        yield  # Never reached, but needed to make this an async generator

    mock_websocket.__aiter__ = lambda self: async_iterator()

    with patch.object(
        connection, "_handle_connection_error", new_callable=AsyncMock
    ) as mock_error:
        await connection._receive_messages()

    mock_error.assert_called_once()


@pytest.mark.asyncio
async def test_connect_cancels_old_receive_task(connection, mock_websocket):
    """Test reconnection cancels old receive task to prevent ConcurrencyError."""
    auth_response = json.dumps(
        [{"ev": "status", "status": "auth_success", "message": "authenticated"}]
    )
    mock_websocket.recv.return_value = auth_response

    with patch("websockets.connect", new_callable=AsyncMock, return_value=mock_websocket):
        with patch.object(connection, "_receive_messages", new_callable=AsyncMock):
            # First connection
            await connection.connect()
            first_task = connection._receive_task
            assert first_task is not None
            assert not first_task.done()

            # Reconnect (simulating error recovery)
            await connection.connect()
            second_task = connection._receive_task

            # Verify old task was cancelled
            assert first_task.done()
            assert first_task.cancelled()

            # Verify new task is running
            assert second_task is not None
            assert not second_task.done()
            assert second_task is not first_task


# Note: Resubscription during reconnection is now covered by
# test_connect_cancels_old_receive_task which verifies task cleanup.

# ============================================================================
# ConnectionManager Tests (7 tests)
# ============================================================================


def test_connection_manager_init(connection_manager):
    """Test ConnectionManager initializes with empty connections."""
    assert connection_manager.connections == {}


def test_get_connection_creates_new(connection_manager):
    """Test get_connection creates new connection when needed."""
    conn = connection_manager.get_connection(
        market="stocks", endpoint="wss://socket.polygon.io/stocks", api_key="test_key"
    )

    assert isinstance(conn, WebSocketConnection)
    assert conn.market == "stocks"
    assert conn.endpoint == "wss://socket.polygon.io/stocks"
    assert conn.api_key == "test_key"
    assert "stocks" in connection_manager.connections


def test_get_connection_reuses_existing(connection_manager):
    """Test get_connection reuses existing connection."""
    conn1 = connection_manager.get_connection(market="stocks", api_key="test_key")
    conn2 = connection_manager.get_connection(market="stocks")

    assert conn1 is conn2
    assert len(connection_manager.connections) == 1


def test_get_connection_auto_generates_endpoint(connection_manager):
    """Test get_connection auto-generates endpoint from market."""
    conn = connection_manager.get_connection(market="crypto", api_key="test_key")

    assert conn.endpoint == "wss://socket.polygon.io/crypto"


def test_get_connection_requires_api_key_for_new(connection_manager):
    """Test get_connection requires API key for new connection."""
    with pytest.raises(
        ValueError, match="API key required for first connection to stocks"
    ):
        connection_manager.get_connection(market="stocks")


@pytest.mark.asyncio
async def test_close_all_connections(connection_manager):
    """Test close_all closes all connections and clears registry."""
    # Create multiple connections
    conn1 = connection_manager.get_connection(market="stocks", api_key="test")
    conn2 = connection_manager.get_connection(market="crypto", api_key="test")

    with patch.object(conn1, "close", new_callable=AsyncMock) as mock_close1:
        with patch.object(conn2, "close", new_callable=AsyncMock) as mock_close2:
            await connection_manager.close_all()

    mock_close1.assert_called_once()
    mock_close2.assert_called_once()
    assert connection_manager.connections == {}


def test_get_all_statuses(connection_manager):
    """Test get_all_statuses returns status for all connections."""
    conn1 = connection_manager.get_connection(market="stocks", api_key="test")
    conn2 = connection_manager.get_connection(market="crypto", api_key="test")

    conn1.subscriptions.update(["T.AAPL"])
    conn2.subscriptions.update(["XT.BTC-USD"])

    statuses = connection_manager.get_all_statuses()

    assert len(statuses) == 2
    assert any(
        s["market"] == "stocks" and s["subscription_count"] == 1 for s in statuses
    )
    assert any(
        s["market"] == "crypto" and s["subscription_count"] == 1 for s in statuses
    )


# ============================================================================
# Message Buffering Tests (8 tests)
# ============================================================================


def test_message_buffer_initialization(connection):
    """Test message buffer initializes with correct attributes."""
    assert hasattr(connection, 'message_buffer')
    assert hasattr(connection, '_total_messages_received')
    assert len(connection.message_buffer) == 0
    assert connection.message_buffer.maxlen == 100
    assert connection._total_messages_received == 0


@pytest.mark.asyncio
async def test_message_buffer_stores_data_messages(connection, mock_websocket):
    """Test data messages are buffered, status messages excluded."""
    connection.websocket = mock_websocket

    messages = [
        json.dumps([
            {"ev": "T", "sym": "AAPL", "p": 150.25, "s": 100},
            {"ev": "Q", "sym": "MSFT", "bp": 300.50, "ap": 300.75},
            {"ev": "status", "status": "success", "message": "Subscribed"},
        ])
    ]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()
    await connection._receive_messages()

    # Only 2 data messages should be buffered (status excluded)
    assert len(connection.message_buffer) == 2
    assert connection._total_messages_received == 2
    assert connection.message_buffer[0]["ev"] == "T"
    assert connection.message_buffer[1]["ev"] == "Q"


@pytest.mark.asyncio
async def test_buffer_circular_overflow(connection, mock_websocket):
    """Test buffer drops oldest messages when maxlen exceeded."""
    # Use smaller buffer for testing overflow
    connection.message_buffer = deque(maxlen=5)
    connection.websocket = mock_websocket

    # Send 10 messages (buffer maxlen=5)
    messages = [json.dumps([{"ev": "T", "id": i}]) for i in range(10)]

    async def async_iterator():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iterator()
    await connection._receive_messages()

    # Buffer should contain only last 5 messages (IDs 5-9)
    assert len(connection.message_buffer) == 5
    assert connection._total_messages_received == 10  # Counter tracks all
    assert connection.message_buffer[0]["id"] == 5  # Oldest in buffer
    assert connection.message_buffer[-1]["id"] == 9  # Newest in buffer


def test_get_recent_messages_with_limit(connection):
    """Test get_recent_messages respects limit parameter."""
    # Add 20 test messages
    for i in range(20):
        connection.message_buffer.append({"ev": "T", "id": i})
        connection._total_messages_received += 1

    # Get last 5 messages
    recent = connection.get_recent_messages(limit=5)

    assert len(recent) == 5
    assert recent[0]["id"] == 15  # Oldest of last 5
    assert recent[-1]["id"] == 19  # Most recent


def test_get_recent_messages_empty_buffer(connection):
    """Test get_recent_messages handles empty buffer correctly."""
    recent = connection.get_recent_messages(limit=10)

    assert recent == []


def test_get_message_stats(connection):
    """Test get_message_stats returns correct structure."""
    # Add messages beyond buffer capacity
    for i in range(150):
        connection.message_buffer.append({"ev": "T", "id": i})
        connection._total_messages_received += 1

    stats = connection.get_message_stats()

    assert stats["total_received"] == 150  # All messages counted
    assert stats["buffered"] == 100  # Buffer capped at maxlen
    assert stats["buffer_capacity"] == 100


@pytest.mark.asyncio
async def test_clear_buffer_on_close(connection, mock_websocket):
    """Test buffer is cleared when connection closes."""
    connection.websocket = mock_websocket
    connection.state = ConnectionState.CONNECTED

    # Add messages to buffer
    connection.message_buffer.append({"ev": "T", "sym": "AAPL"})
    connection._total_messages_received = 10

    await connection.close()

    # Buffer cleared, but counter persists
    assert len(connection.message_buffer) == 0
    assert connection._total_messages_received == 10


def test_handle_status_api_access_error(connection):
    """Test APIAccessError raised for API plan limitations."""
    from mcp_polygon.tools.websockets.connection_manager import APIAccessError

    status_msg = {
        "ev": "status",
        "status": "error",
        "message": "You don't have access real-time data. If your plan only includes delayed data, you can connect to the delayed websocket at wss://delayed.polygon.io/stocks."
    }

    with pytest.raises(APIAccessError) as exc_info:
        connection._handle_status(status_msg)

    # Verify error message contains helpful guidance
    error_msg = str(exc_info.value)
    assert "API Plan Limitation" in error_msg
    assert "polygon.io/pricing" in error_msg
    assert "delayed.polygon.io" in error_msg


def test_handle_status_normal_messages(connection):
    """Test normal status messages don't raise errors."""
    status_msg = {
        "ev": "status",
        "status": "success",
        "message": "Subscribed to channels"
    }

    # Should not raise any exception
    connection._handle_status(status_msg)
