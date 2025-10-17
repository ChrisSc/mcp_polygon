"""
Unit tests for WebSocket stocks market tools.

Tests all 6 tools in the stocks module:
- start_stocks_stream: Start real-time data stream
- stop_stocks_stream: Stop active stream
- get_stocks_stream_status: Get connection status
- subscribe_stocks_channels: Add subscriptions
- unsubscribe_stocks_channels: Remove subscriptions
- list_stocks_subscriptions: List all subscriptions
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mcp.server.fastmcp import FastMCP

from mcp_polygon.tools.websockets import stocks
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
    conn.market = "stocks"
    conn.endpoint = "wss://socket.polygon.io/stocks"
    conn.state = ConnectionState.CONNECTED
    conn.subscriptions = {"T.AAPL", "Q.MSFT"}

    # Mock async methods
    conn.connect = AsyncMock()
    conn.subscribe = AsyncMock()
    conn.unsubscribe = AsyncMock()
    conn.close = AsyncMock()

    # Mock get_status
    conn.get_status = Mock(return_value={
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": ["T.AAPL", "Q.MSFT"],
        "subscription_count": 2,
    })

    return conn


@pytest.fixture
def mock_connection_manager(mock_websocket_connection):
    """Mock ConnectionManager with proper connection behavior."""
    manager = Mock(spec=ConnectionManager)
    manager.connections = {"stocks": mock_websocket_connection}

    # Mock get_connection to return mock connection
    manager.get_connection = Mock(return_value=mock_websocket_connection)

    return manager


@pytest.fixture
def mcp_server(mock_connection_manager):
    """FastMCP instance with stocks tools registered."""
    mcp = FastMCP("test-stocks")
    stocks.register_tools(mcp, mock_connection_manager)
    return mcp


# ============================================================================
# start_stocks_stream Tests (5 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_start_stocks_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful stocks stream start with valid API key."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "start_stocks_stream",
        {
            "channels": ["T.AAPL", "Q.MSFT"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Started stocks WebSocket stream" in result_text
    assert "T.AAPL, Q.MSFT" in result_text

    # Verify connection manager called correctly
    mock_connection_manager.get_connection.assert_called_once_with(
        "stocks",
        endpoint="wss://socket.polygon.io/stocks",
        api_key="test_api_key"
    )

    # Verify connection methods called
    mock_websocket_connection.connect.assert_awaited_once()
    mock_websocket_connection.subscribe.assert_awaited_once_with(["T.AAPL", "Q.MSFT"])


@pytest.mark.asyncio
async def test_start_stocks_stream_with_custom_endpoint(mock_connection_manager, mock_websocket_connection):
    """Test stream start with custom delayed endpoint."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)
    custom_endpoint = "wss://delayed.polygon.io/stocks"

    # Act
    result = await mcp.call_tool(
        "start_stocks_stream",
        {
            "channels": ["T.AAPL"],
            "api_key": "test_api_key",
            "endpoint": custom_endpoint
        }
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert custom_endpoint in result_text

    # Verify custom endpoint passed to connection manager
    mock_connection_manager.get_connection.assert_called_once_with(
        "stocks",
        endpoint=custom_endpoint,
        api_key="test_api_key"
    )


@pytest.mark.asyncio
async def test_start_stocks_stream_uses_env_api_key(mock_connection_manager, mock_websocket_connection):
    """Test stream start uses POLYGON_API_KEY environment variable when not provided."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    with patch.dict(os.environ, {"POLYGON_API_KEY": "env_api_key"}):
        # Act
        result = await mcp.call_tool(
            "start_stocks_stream",
            {"channels": ["T.AAPL"]}
        )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text

    # Verify env API key used
    mock_connection_manager.get_connection.assert_called_once_with(
        "stocks",
        endpoint="wss://socket.polygon.io/stocks",
        api_key="env_api_key"
    )


@pytest.mark.asyncio
async def test_start_stocks_stream_multiple_channels(mock_connection_manager, mock_websocket_connection):
    """Test stream start with multiple channel subscriptions."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)
    channels = ["T.AAPL", "Q.AAPL", "AM.AAPL", "T.MSFT", "Q.MSFT"]

    # Act
    result = await mcp.call_tool(
        "start_stocks_stream",
        {
            "channels": channels,
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    result_text = str(result)
    assert "5" in result_text or all(ch in result_text for ch in channels[:3])
    mock_websocket_connection.subscribe.assert_awaited_once_with(channels)


@pytest.mark.asyncio
async def test_start_stocks_stream_connection_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when connection fails."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock connection failure
    mock_websocket_connection.connect.side_effect = Exception("Connection timeout")

    # Act
    result = await mcp.call_tool(
        "start_stocks_stream",
        {
            "channels": ["T.AAPL"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to start stocks stream" in result_text
    assert "Connection timeout" in result_text


# ============================================================================
# stop_stocks_stream Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_stop_stocks_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful stop of active stream."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("stop_stocks_stream", {})

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Stopped stocks WebSocket stream" in result_text

    # Verify connection closed
    mock_connection_manager.get_connection.assert_called_once_with("stocks")
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_stocks_stream_no_active_connection(mock_connection_manager):
    """Test stop when no stream exists (KeyError handling)."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("stocks")

    # Act
    result = await mcp.call_tool("stop_stocks_stream", {})

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active stocks WebSocket connection" in result_text


@pytest.mark.asyncio
async def test_stop_stocks_stream_close_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when close operation fails."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock close failure
    mock_websocket_connection.close.side_effect = Exception("Close error")

    # Act
    result = await mcp.call_tool("stop_stocks_stream", {})

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to stop stocks stream" in result_text
    assert "Close error" in result_text


# ============================================================================
# get_stocks_stream_status Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_get_stocks_stream_status_active(mock_connection_manager, mock_websocket_connection):
    """Test status retrieval for active connection."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("get_stocks_stream_status", {})

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text or "STOCKS" in result_text
    assert "connected" in result_text.lower()
    assert "wss://socket.polygon.io/stocks" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_get_stocks_stream_status_no_connection(mock_connection_manager):
    """Test status when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("stocks")

    # Act
    result = await mcp.call_tool("get_stocks_stream_status", {})

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active stocks WebSocket connection" in result_text


# ============================================================================
# subscribe_stocks_channels Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_stocks_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful subscription to new channels."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)
    new_channels = ["T.NVDA", "Q.AMD"]

    # Act
    result = await mcp.call_tool(
        "subscribe_stocks_channels",
        {"channels": new_channels}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Added 2 subscriptions" in result_text
    assert "Total subscriptions: 2" in result_text

    # Verify subscribe called
    mock_websocket_connection.subscribe.assert_awaited_once_with(new_channels)
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_subscribe_stocks_channels_single(mock_connection_manager, mock_websocket_connection):
    """Test subscribing to a single channel."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "subscribe_stocks_channels",
        {"channels": ["AM.*"]}  # Subscribe to all minute aggregates
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Added 1 subscriptions" in result_text
    mock_websocket_connection.subscribe.assert_awaited_once_with(["AM.*"])


@pytest.mark.asyncio
async def test_subscribe_stocks_channels_no_stream(mock_connection_manager):
    """Test subscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("stocks")

    # Act
    result = await mcp.call_tool(
        "subscribe_stocks_channels",
        {"channels": ["T.AAPL"]}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active stocks stream" in result_text
    assert "Use start_stocks_stream() first" in result_text


@pytest.mark.asyncio
async def test_subscribe_stocks_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when subscription fails."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock subscription failure
    mock_websocket_connection.subscribe.side_effect = Exception("Invalid channel format")

    # Act
    result = await mcp.call_tool(
        "subscribe_stocks_channels",
        {"channels": ["INVALID"]}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to subscribe" in result_text
    assert "Invalid channel format" in result_text


# ============================================================================
# unsubscribe_stocks_channels Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_unsubscribe_stocks_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful unsubscription from channels."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Update mock status after unsubscribe
    mock_websocket_connection.get_status.return_value = {
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": ["Q.MSFT"],  # Only one remaining
        "subscription_count": 1,
    }

    # Act
    result = await mcp.call_tool(
        "unsubscribe_stocks_channels",
        {"channels": ["T.AAPL"]}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Removed 1 subscriptions" in result_text
    assert "Total subscriptions: 1" in result_text

    # Verify unsubscribe called
    mock_websocket_connection.unsubscribe.assert_awaited_once_with(["T.AAPL"])
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_unsubscribe_stocks_channels_no_stream(mock_connection_manager):
    """Test unsubscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("stocks")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_stocks_channels",
        {"channels": ["T.AAPL"]}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active stocks stream" in result_text
    assert "Use start_stocks_stream() first" in result_text


@pytest.mark.asyncio
async def test_unsubscribe_stocks_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when unsubscription fails."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock unsubscribe failure
    mock_websocket_connection.unsubscribe.side_effect = Exception("Unsubscribe error")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_stocks_channels",
        {"channels": ["T.AAPL"]}
    )

    # Assert
    result_text = str(result)

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to unsubscribe" in result_text
    assert "Unsubscribe error" in result_text


# ============================================================================
# list_stocks_subscriptions Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_list_stocks_subscriptions_active(mock_connection_manager, mock_websocket_connection):
    """Test listing subscriptions for active stream."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("list_stocks_subscriptions", {})

    # Assert
    result_text = str(result)

    # Assert
    assert "Stocks Stream Subscriptions" in result_text
    assert "2 total" in result_text
    assert "T.AAPL" in result_text or "Q.MSFT" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_list_stocks_subscriptions_grouped_by_type(mock_connection_manager, mock_websocket_connection):
    """Test subscriptions are grouped by channel type."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Update mock with multiple channel types
    mock_websocket_connection.get_status.return_value = {
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": ["T.AAPL", "T.MSFT", "Q.AAPL", "AM.AAPL", "LULD.TSLA"],
        "subscription_count": 5,
    }

    # Act
    result = await mcp.call_tool("list_stocks_subscriptions", {})

    # Assert
    result_text = str(result)

    # Assert
    assert "Trades" in result_text
    assert "Quotes" in result_text
    assert "Minute Aggregates" in result_text
    assert "Limit Up/Limit Down" in result_text


@pytest.mark.asyncio
async def test_list_stocks_subscriptions_empty(mock_connection_manager, mock_websocket_connection):
    """Test listing when no subscriptions exist."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Update mock with no subscriptions
    mock_websocket_connection.get_status.return_value = {
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": [],
        "subscription_count": 0,
    }

    # Act
    result = await mcp.call_tool("list_stocks_subscriptions", {})

    # Assert
    result_text = str(result)

    # Assert
    assert "No active subscriptions" in result_text


@pytest.mark.asyncio
async def test_list_stocks_subscriptions_no_connection(mock_connection_manager):
    """Test list when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("stocks")

    # Act
    result = await mcp.call_tool("list_stocks_subscriptions", {})

    # Assert
    result_text = str(result)

    # Assert
    assert "No active stocks WebSocket connection" in result_text


# ============================================================================
# Integration Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_complete_workflow_start_subscribe_stop(mock_connection_manager, mock_websocket_connection):
    """Test complete workflow: start -> subscribe -> stop."""
    # Arrange
    mcp = FastMCP("test")
    stocks.register_tools(mcp, mock_connection_manager)

    # Act & Assert - Start
    result1 = await mcp.call_tool(
        "start_stocks_stream",
        {
            "channels": ["T.AAPL"],
            "api_key": "test_api_key"
        }
    )
    result1_text = str(result1)
    assert "✓" in result1_text
    assert "Started stocks WebSocket stream" in result1_text

    # Act & Assert - Subscribe
    mock_websocket_connection.subscribe.reset_mock()
    result2 = await mcp.call_tool(
        "subscribe_stocks_channels",
        {"channels": ["Q.AAPL"]}
    )
    result2_text = str(result2)
    assert "✓" in result2_text
    assert "Added 1 subscriptions" in result2_text

    # Act & Assert - Stop
    result3 = await mcp.call_tool("stop_stocks_stream", {})
    result3_text = str(result3)
    assert "✓" in result3_text
    assert "Stopped stocks WebSocket stream" in result3_text

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
    stocks.register_tools(mcp, mock_connection_manager)

    # Assert - Verify all tools registered
    tool_names = [tool.name for tool in mcp._tool_manager._tools.values()]

    expected_tools = [
        "start_stocks_stream",
        "stop_stocks_stream",
        "get_stocks_stream_status",
        "subscribe_stocks_channels",
        "unsubscribe_stocks_channels",
        "list_stocks_subscriptions",
    ]

    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Tool {tool_name} not registered"
