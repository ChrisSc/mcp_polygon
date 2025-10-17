"""
Unit tests for WebSocket futures market tools.

Tests all 6 tools in the futures module:
- start_futures_stream: Start real-time data stream
- stop_futures_stream: Stop active stream
- get_futures_stream_status: Get connection status
- subscribe_futures_channels: Add subscriptions
- unsubscribe_futures_channels: Remove subscriptions
- list_futures_subscriptions: List all subscriptions
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mcp.server.fastmcp import FastMCP

from mcp_polygon.tools.websockets import futures
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
    conn.market = "futures"
    conn.endpoint = "wss://socket.polygon.io/futures"
    conn.state = ConnectionState.CONNECTED
    conn.subscriptions = {"T.ESZ24", "Q.GCZ24"}

    # Mock async methods
    conn.connect = AsyncMock()
    conn.subscribe = AsyncMock()
    conn.unsubscribe = AsyncMock()
    conn.close = AsyncMock()

    # Mock get_status
    conn.get_status = Mock(return_value={
        "market": "futures",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/futures",
        "subscriptions": ["T.ESZ24", "Q.GCZ24"],
        "subscription_count": 2,
    })

    return conn


@pytest.fixture
def mock_connection_manager(mock_websocket_connection):
    """Mock ConnectionManager with proper connection behavior."""
    manager = Mock(spec=ConnectionManager)
    manager.connections = {"futures": mock_websocket_connection}

    # Mock get_connection to return mock connection
    manager.get_connection = Mock(return_value=mock_websocket_connection)

    return manager


@pytest.fixture
def mcp_server(mock_connection_manager):
    """FastMCP instance with futures tools registered."""
    mcp = FastMCP("test-futures")
    futures.register_tools(mcp, mock_connection_manager)
    return mcp


# ============================================================================
# start_futures_stream Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_start_futures_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful futures stream start with valid API key."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "start_futures_stream",
        {
            "channels": ["T.ESZ24", "Q.GCZ24"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Started futures WebSocket stream" in result_text
    assert "T.ESZ24, Q.GCZ24" in result_text

    # Verify connection manager called correctly
    mock_connection_manager.get_connection.assert_called_once_with(
        "futures",
        endpoint="wss://socket.polygon.io/futures",
        api_key="test_api_key"
    )

    # Verify connection methods called
    mock_websocket_connection.connect.assert_awaited_once()
    mock_websocket_connection.subscribe.assert_awaited_once_with(["T.ESZ24", "Q.GCZ24"])


@pytest.mark.asyncio
async def test_start_futures_stream_with_custom_endpoint(mock_connection_manager, mock_websocket_connection):
    """Test stream start with custom delayed endpoint."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)
    custom_endpoint = "wss://delayed.polygon.io/futures"

    # Act
    result = await mcp.call_tool(
        "start_futures_stream",
        {
            "channels": ["T.ESZ24"],
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
        "futures",
        endpoint=custom_endpoint,
        api_key="test_api_key"
    )


@pytest.mark.asyncio
async def test_start_futures_stream_uses_env_api_key(mock_connection_manager, mock_websocket_connection):
    """Test stream start uses POLYGON_API_KEY environment variable when not provided."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    with patch.dict(os.environ, {"POLYGON_API_KEY": "env_api_key"}):
        # Act
        result = await mcp.call_tool(
            "start_futures_stream",
            {"channels": ["T.ESZ24"]}
        )

    # Assert
    result_text = str(result)
    assert "✓" in result_text

    # Verify env API key used
    mock_connection_manager.get_connection.assert_called_once_with(
        "futures",
        endpoint="wss://socket.polygon.io/futures",
        api_key="env_api_key"
    )


@pytest.mark.asyncio
async def test_start_futures_stream_connection_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when connection fails."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock connection failure
    mock_websocket_connection.connect.side_effect = Exception("Connection timeout")

    # Act
    result = await mcp.call_tool(
        "start_futures_stream",
        {
            "channels": ["T.ESZ24"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to start futures stream" in result_text
    assert "Connection timeout" in result_text


# ============================================================================
# stop_futures_stream Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_stop_futures_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful stop of active stream."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("stop_futures_stream", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Stopped futures WebSocket stream" in result_text

    # Verify connection closed
    mock_connection_manager.get_connection.assert_called_once_with("futures")
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_futures_stream_no_active_connection(mock_connection_manager):
    """Test stop when no stream exists (KeyError handling)."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("futures")

    # Act
    result = await mcp.call_tool("stop_futures_stream", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active futures WebSocket connection" in result_text


# ============================================================================
# get_futures_stream_status Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_get_futures_stream_status_active(mock_connection_manager, mock_websocket_connection):
    """Test status retrieval for active connection."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("get_futures_stream_status", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text or "FUTURES" in result_text
    assert "connected" in result_text.lower()
    assert "wss://socket.polygon.io/futures" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_get_futures_stream_status_no_connection(mock_connection_manager):
    """Test status when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("futures")

    # Act
    result = await mcp.call_tool("get_futures_stream_status", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active futures WebSocket connection" in result_text


# ============================================================================
# subscribe_futures_channels Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_futures_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful subscription to new channels."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)
    new_channels = ["T.NQZ24", "Q.CLZ24"]

    # Act
    result = await mcp.call_tool(
        "subscribe_futures_channels",
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
async def test_subscribe_futures_channels_no_stream(mock_connection_manager):
    """Test subscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("futures")

    # Act
    result = await mcp.call_tool(
        "subscribe_futures_channels",
        {"channels": ["T.ESZ24"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active futures stream" in result_text
    assert "Use start_futures_stream() first" in result_text


@pytest.mark.asyncio
async def test_subscribe_futures_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when subscription fails."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock subscription failure
    mock_websocket_connection.subscribe.side_effect = Exception("Invalid channel format")

    # Act
    result = await mcp.call_tool(
        "subscribe_futures_channels",
        {"channels": ["INVALID"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to subscribe" in result_text
    assert "Invalid channel format" in result_text


# ============================================================================
# unsubscribe_futures_channels Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_unsubscribe_futures_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful unsubscription from channels."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Update mock status after unsubscribe
    mock_websocket_connection.get_status.return_value = {
        "market": "futures",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/futures",
        "subscriptions": ["Q.GCZ24"],  # Only one remaining
        "subscription_count": 1,
    }

    # Act
    result = await mcp.call_tool(
        "unsubscribe_futures_channels",
        {"channels": ["T.ESZ24"]}
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Removed 1 subscriptions" in result_text
    assert "Total subscriptions: 1" in result_text

    # Verify unsubscribe called
    mock_websocket_connection.unsubscribe.assert_awaited_once_with(["T.ESZ24"])
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_unsubscribe_futures_channels_no_stream(mock_connection_manager):
    """Test unsubscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("futures")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_futures_channels",
        {"channels": ["T.ESZ24"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active futures stream" in result_text
    assert "Use start_futures_stream() first" in result_text


# ============================================================================
# list_futures_subscriptions Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_list_futures_subscriptions_active(mock_connection_manager, mock_websocket_connection):
    """Test listing subscriptions for active stream."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("list_futures_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Futures Stream Subscriptions" in result_text
    assert "2 total" in result_text
    assert "T.ESZ24" in result_text or "Q.GCZ24" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_list_futures_subscriptions_grouped_by_type(mock_connection_manager, mock_websocket_connection):
    """Test subscriptions are grouped by channel type (4 groups: T., Q., AM., AS.)."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Update mock with multiple channel types (NO FMV for futures)
    mock_websocket_connection.get_status.return_value = {
        "market": "futures",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/futures",
        "subscriptions": [
            "T.ESZ24", "T.GCZ24",  # Trades
            "Q.ESZ24",              # Quotes
            "AM.ESZ24",             # Minute agg
            "AS.ESZ24"              # Second agg
        ],
        "subscription_count": 5,
    }

    # Act
    result = await mcp.call_tool("list_futures_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Trades" in result_text
    assert "Quotes" in result_text
    assert "Minute Aggregates" in result_text
    assert "Second Aggregates" in result_text


@pytest.mark.asyncio
async def test_list_futures_subscriptions_empty(mock_connection_manager, mock_websocket_connection):
    """Test listing when no subscriptions exist."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Update mock with no subscriptions
    mock_websocket_connection.get_status.return_value = {
        "market": "futures",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/futures",
        "subscriptions": [],
        "subscription_count": 0,
    }

    # Act
    result = await mcp.call_tool("list_futures_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active subscriptions" in result_text


@pytest.mark.asyncio
async def test_list_futures_subscriptions_no_connection(mock_connection_manager):
    """Test list when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("futures")

    # Act
    result = await mcp.call_tool("list_futures_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active futures WebSocket connection" in result_text


# ============================================================================
# Integration Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_complete_workflow_start_subscribe_stop(mock_connection_manager, mock_websocket_connection):
    """Test complete workflow: start -> subscribe -> stop."""
    # Arrange
    mcp = FastMCP("test")
    futures.register_tools(mcp, mock_connection_manager)

    # Act & Assert - Start
    result1 = await mcp.call_tool(
        "start_futures_stream",
        {
            "channels": ["T.ESZ24"],
            "api_key": "test_api_key"
        }
    )
    result1_text = str(result1)
    assert "✓" in result1_text
    assert "Started futures WebSocket stream" in result1_text

    # Act & Assert - Subscribe
    mock_websocket_connection.subscribe.reset_mock()
    result2 = await mcp.call_tool(
        "subscribe_futures_channels",
        {"channels": ["Q.ESZ24"]}
    )
    result2_text = str(result2)
    assert "✓" in result2_text
    assert "Added 1 subscriptions" in result2_text

    # Act & Assert - Stop
    result3 = await mcp.call_tool("stop_futures_stream", {})
    result3_text = str(result3)
    assert "✓" in result3_text
    assert "Stopped futures WebSocket stream" in result3_text

    # Verify call sequence
    mock_websocket_connection.connect.assert_awaited()
    assert mock_websocket_connection.subscribe.await_count == 1
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_tool_registration_all_tools_available(mock_connection_manager):
    """Test that all 6 tools are registered correctly."""
    # Arrange
    mcp = FastMCP("test")

    # Act
    futures.register_tools(mcp, mock_connection_manager)

    # Assert - Verify all tools registered
    tool_names = [tool.name for tool in mcp._tool_manager._tools.values()]

    expected_tools = [
        "start_futures_stream",
        "stop_futures_stream",
        "get_futures_stream_status",
        "subscribe_futures_channels",
        "unsubscribe_futures_channels",
        "list_futures_subscriptions",
    ]

    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Tool {tool_name} not registered"
