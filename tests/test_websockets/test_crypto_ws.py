"""
Unit tests for WebSocket crypto market tools.

Tests all 6 tools in the crypto module:
- start_crypto_stream: Start real-time data stream
- stop_crypto_stream: Stop active stream
- get_crypto_stream_status: Get connection status
- subscribe_crypto_channels: Add subscriptions
- unsubscribe_crypto_channels: Remove subscriptions
- list_crypto_subscriptions: List all subscriptions
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mcp.server.fastmcp import FastMCP

from mcp_polygon.tools.websockets import crypto
from mcp_polygon.tools.websockets.connection_manager import (
    ConnectionState,
    WebSocketConnection,
    ConnectionManager,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_websocket_connection():
    """Mock WebSocketConnection with proper async methods."""
    conn = Mock(spec=WebSocketConnection)
    conn.market = "crypto"
    conn.endpoint = "wss://socket.polygon.io/crypto"
    conn.state = ConnectionState.CONNECTED
    conn.subscriptions = {"XT.BTC-USD", "XQ.ETH-USD"}

    # Mock async methods
    conn.connect = AsyncMock()
    conn.subscribe = AsyncMock()
    conn.unsubscribe = AsyncMock()
    conn.close = AsyncMock()

    # Mock get_status
    conn.get_status = Mock(return_value={
        "market": "crypto",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/crypto",
        "subscriptions": ["XT.BTC-USD", "XQ.ETH-USD"],
        "subscription_count": 2,
    })

    return conn


@pytest.fixture
def mock_connection_manager(mock_websocket_connection):
    """Mock ConnectionManager with proper connection behavior."""
    manager = Mock(spec=ConnectionManager)
    manager.connections = {"crypto": mock_websocket_connection}

    # Mock get_connection to return mock connection
    manager.get_connection = Mock(return_value=mock_websocket_connection)

    return manager


@pytest.fixture
def mcp_server(mock_connection_manager):
    """FastMCP instance with crypto tools registered."""
    mcp = FastMCP("test-crypto")
    crypto.register_tools(mcp, mock_connection_manager)
    return mcp


# ============================================================================
# start_crypto_stream Tests (5 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_start_crypto_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful crypto stream start with valid API key."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "start_crypto_stream",
        {
            "channels": ["XT.BTC-USD", "XQ.ETH-USD"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Started crypto WebSocket stream" in result_text
    assert "XT.BTC-USD, XQ.ETH-USD" in result_text

    # Verify connection manager called correctly
    mock_connection_manager.get_connection.assert_called_once_with(
        "crypto",
        endpoint="wss://socket.polygon.io/crypto",
        api_key="test_api_key"
    )

    # Verify connection methods called
    mock_websocket_connection.connect.assert_awaited_once()
    mock_websocket_connection.subscribe.assert_awaited_once_with(["XT.BTC-USD", "XQ.ETH-USD"])


@pytest.mark.asyncio
async def test_start_crypto_stream_with_custom_endpoint(mock_connection_manager, mock_websocket_connection):
    """Test stream start with custom delayed endpoint."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)
    custom_endpoint = "wss://delayed.polygon.io/crypto"

    # Act
    result = await mcp.call_tool(
        "start_crypto_stream",
        {
            "channels": ["XT.BTC-USD"],
            "api_key": "test_api_key",
            "endpoint": custom_endpoint
        }
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert custom_endpoint in result_text

    # Verify custom endpoint passed to connection manager
    mock_connection_manager.get_connection.assert_called_once_with(
        "crypto",
        endpoint=custom_endpoint,
        api_key="test_api_key"
    )


@pytest.mark.asyncio
async def test_start_crypto_stream_uses_env_api_key(mock_connection_manager, mock_websocket_connection):
    """Test stream start uses POLYGON_API_KEY environment variable when not provided."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    with patch.dict(os.environ, {"POLYGON_API_KEY": "env_api_key"}):
        # Act
        result = await mcp.call_tool(
            "start_crypto_stream",
            {"channels": ["XT.BTC-USD"]}
        )

    # Assert
    result_text = str(result)
    assert "✓" in result_text

    # Verify env API key used
    mock_connection_manager.get_connection.assert_called_once_with(
        "crypto",
        endpoint="wss://socket.polygon.io/crypto",
        api_key="env_api_key"
    )


@pytest.mark.asyncio
async def test_start_crypto_stream_multiple_channels(mock_connection_manager, mock_websocket_connection):
    """Test stream start with multiple channel subscriptions."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)
    channels = ["XT.BTC-USD", "XQ.BTC-USD", "XA.BTC-USD", "XT.ETH-USD", "XQ.ETH-USD"]

    # Act
    result = await mcp.call_tool(
        "start_crypto_stream",
        {
            "channels": channels,
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "5" in result_text or all(ch in result_text for ch in channels[:3])
    mock_websocket_connection.subscribe.assert_awaited_once_with(channels)


@pytest.mark.asyncio
async def test_start_crypto_stream_connection_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when connection fails."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock connection failure
    mock_websocket_connection.connect.side_effect = Exception("Connection timeout")

    # Act
    result = await mcp.call_tool(
        "start_crypto_stream",
        {
            "channels": ["XT.BTC-USD"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to start crypto stream" in result_text
    assert "Connection timeout" in result_text


# ============================================================================
# stop_crypto_stream Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_stop_crypto_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful stop of active stream."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("stop_crypto_stream", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Stopped crypto WebSocket stream" in result_text

    # Verify connection closed
    mock_connection_manager.get_connection.assert_called_once_with("crypto")
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_crypto_stream_no_active_connection(mock_connection_manager):
    """Test stop when no stream exists (KeyError handling)."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("crypto")

    # Act
    result = await mcp.call_tool("stop_crypto_stream", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active crypto WebSocket connection" in result_text


@pytest.mark.asyncio
async def test_stop_crypto_stream_close_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when close operation fails."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock close failure
    mock_websocket_connection.close.side_effect = Exception("Close error")

    # Act
    result = await mcp.call_tool("stop_crypto_stream", {})

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to stop crypto stream" in result_text
    assert "Close error" in result_text


# ============================================================================
# get_crypto_stream_status Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_get_crypto_stream_status_active(mock_connection_manager, mock_websocket_connection):
    """Test status retrieval for active connection."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("get_crypto_stream_status", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text or "CRYPTO" in result_text
    assert "connected" in result_text.lower()
    assert "wss://socket.polygon.io/crypto" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_get_crypto_stream_status_no_connection(mock_connection_manager):
    """Test status when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("crypto")

    # Act
    result = await mcp.call_tool("get_crypto_stream_status", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active crypto WebSocket connection" in result_text


# ============================================================================
# subscribe_crypto_channels Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_crypto_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful subscription to new channels."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)
    new_channels = ["XT.SOL-USD", "XQ.ADA-USD"]

    # Act
    result = await mcp.call_tool(
        "subscribe_crypto_channels",
        {"channels": new_channels}
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Added 2 subscriptions" in result_text
    assert "Total subscriptions: 2" in result_text

    # Verify subscribe called
    mock_websocket_connection.subscribe.assert_awaited_once_with(new_channels)
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_subscribe_crypto_channels_single(mock_connection_manager, mock_websocket_connection):
    """Test subscribing to a single channel."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "subscribe_crypto_channels",
        {"channels": ["XA.*"]}  # Subscribe to all minute aggregates
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Added 1 subscriptions" in result_text
    mock_websocket_connection.subscribe.assert_awaited_once_with(["XA.*"])


@pytest.mark.asyncio
async def test_subscribe_crypto_channels_no_stream(mock_connection_manager):
    """Test subscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("crypto")

    # Act
    result = await mcp.call_tool(
        "subscribe_crypto_channels",
        {"channels": ["XT.BTC-USD"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active crypto stream" in result_text
    assert "Use start_crypto_stream() first" in result_text


@pytest.mark.asyncio
async def test_subscribe_crypto_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when subscription fails."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock subscription failure
    mock_websocket_connection.subscribe.side_effect = Exception("Invalid channel format")

    # Act
    result = await mcp.call_tool(
        "subscribe_crypto_channels",
        {"channels": ["INVALID"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to subscribe" in result_text
    assert "Invalid channel format" in result_text


# ============================================================================
# unsubscribe_crypto_channels Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_unsubscribe_crypto_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful unsubscription from channels."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Update mock status after unsubscribe
    mock_websocket_connection.get_status.return_value = {
        "market": "crypto",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/crypto",
        "subscriptions": ["XQ.ETH-USD"],  # Only one remaining
        "subscription_count": 1,
    }

    # Act
    result = await mcp.call_tool(
        "unsubscribe_crypto_channels",
        {"channels": ["XT.BTC-USD"]}
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Removed 1 subscriptions" in result_text
    assert "Total subscriptions: 1" in result_text

    # Verify unsubscribe called
    mock_websocket_connection.unsubscribe.assert_awaited_once_with(["XT.BTC-USD"])
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_unsubscribe_crypto_channels_no_stream(mock_connection_manager):
    """Test unsubscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("crypto")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_crypto_channels",
        {"channels": ["XT.BTC-USD"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active crypto stream" in result_text
    assert "Use start_crypto_stream() first" in result_text


@pytest.mark.asyncio
async def test_unsubscribe_crypto_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when unsubscription fails."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock unsubscribe failure
    mock_websocket_connection.unsubscribe.side_effect = Exception("Unsubscribe error")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_crypto_channels",
        {"channels": ["XT.BTC-USD"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to unsubscribe" in result_text
    assert "Unsubscribe error" in result_text


# ============================================================================
# list_crypto_subscriptions Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_list_crypto_subscriptions_active(mock_connection_manager, mock_websocket_connection):
    """Test listing subscriptions for active stream."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("list_crypto_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Crypto Stream Subscriptions" in result_text
    assert "2 total" in result_text
    assert "XT.BTC-USD" in result_text or "XQ.ETH-USD" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_list_crypto_subscriptions_grouped_by_type(mock_connection_manager, mock_websocket_connection):
    """Test subscriptions are grouped by channel type."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Update mock with multiple channel types
    mock_websocket_connection.get_status.return_value = {
        "market": "crypto",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/crypto",
        "subscriptions": [
            "XT.BTC-USD", "XT.ETH-USD",  # Trades
            "XQ.BTC-USD", "XQ.ETH-USD",  # Quotes
            "XA.BTC-USD",                 # Minute agg
            "XAS.BTC-USD",                # Second agg
            "FMV.BTC-USD"                 # Fair value
        ],
        "subscription_count": 7,
    }

    # Act
    result = await mcp.call_tool("list_crypto_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Trades" in result_text
    assert "Quotes" in result_text
    assert "Minute Aggregates" in result_text
    assert "Second Aggregates" in result_text
    assert "Fair Market Value" in result_text


@pytest.mark.asyncio
async def test_list_crypto_subscriptions_empty(mock_connection_manager, mock_websocket_connection):
    """Test listing when no subscriptions exist."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Update mock with no subscriptions
    mock_websocket_connection.get_status.return_value = {
        "market": "crypto",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/crypto",
        "subscriptions": [],
        "subscription_count": 0,
    }

    # Act
    result = await mcp.call_tool("list_crypto_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active subscriptions" in result_text


@pytest.mark.asyncio
async def test_list_crypto_subscriptions_no_connection(mock_connection_manager):
    """Test list when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("crypto")

    # Act
    result = await mcp.call_tool("list_crypto_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active crypto WebSocket connection" in result_text


# ============================================================================
# Integration Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_complete_workflow_start_subscribe_stop(mock_connection_manager, mock_websocket_connection):
    """Test complete workflow: start -> subscribe -> stop."""
    # Arrange
    mcp = FastMCP("test")
    crypto.register_tools(mcp, mock_connection_manager)

    # Act & Assert - Start
    result1 = await mcp.call_tool(
        "start_crypto_stream",
        {
            "channels": ["XT.BTC-USD"],
            "api_key": "test_api_key"
        }
    )
    result1_text = str(result1)
    assert "✓" in result1_text
    assert "Started crypto WebSocket stream" in result1_text

    # Act & Assert - Subscribe
    mock_websocket_connection.subscribe.reset_mock()
    result2 = await mcp.call_tool(
        "subscribe_crypto_channels",
        {"channels": ["XQ.BTC-USD"]}
    )
    result2_text = str(result2)
    assert "✓" in result2_text
    assert "Added 1 subscriptions" in result2_text

    # Act & Assert - Stop
    result3 = await mcp.call_tool("stop_crypto_stream", {})
    result3_text = str(result3)
    assert "✓" in result3_text
    assert "Stopped crypto WebSocket stream" in result3_text

    # Verify call sequence
    mock_websocket_connection.connect.assert_awaited()
    # Subscribe called once after reset (initial call + new subscription, but we reset before the second one)
    assert mock_websocket_connection.subscribe.await_count == 1  # After reset, only new subscription
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_registration_all_tools_available(mock_connection_manager):
    """Test that all 6 tools are registered correctly."""
    # Arrange
    mcp = FastMCP("test")

    # Act
    crypto.register_tools(mcp, mock_connection_manager)

    # Assert - Verify all tools registered
    tool_names = [tool.name for tool in mcp._tool_manager._tools.values()]

    expected_tools = [
        "start_crypto_stream",
        "stop_crypto_stream",
        "get_crypto_stream_status",
        "subscribe_crypto_channels",
        "unsubscribe_crypto_channels",
        "list_crypto_subscriptions",
    ]

    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Tool {tool_name} not registered"
