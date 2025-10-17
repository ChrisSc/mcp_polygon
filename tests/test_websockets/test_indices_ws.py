"""
Unit tests for WebSocket indices market tools.

Tests all 6 tools in the indices module:
- start_indices_stream: Start real-time data stream
- stop_indices_stream: Stop active stream
- get_indices_stream_status: Get connection status
- subscribe_indices_channels: Add subscriptions
- unsubscribe_indices_channels: Remove subscriptions
- list_indices_subscriptions: List all subscriptions
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
from mcp.server.fastmcp import FastMCP

from mcp_polygon.tools.websockets import indices
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
    conn.market = "indices"
    conn.endpoint = "wss://socket.polygon.io/indices"
    conn.state = ConnectionState.CONNECTED
    conn.subscriptions = {"V.I:SPX", "AM.I:DJI"}

    # Mock async methods
    conn.connect = AsyncMock()
    conn.subscribe = AsyncMock()
    conn.unsubscribe = AsyncMock()
    conn.close = AsyncMock()

    # Mock get_status
    conn.get_status = Mock(return_value={
        "market": "indices",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/indices",
        "subscriptions": ["V.I:SPX", "AM.I:DJI"],
        "subscription_count": 2,
    })

    return conn


@pytest.fixture
def mock_connection_manager(mock_websocket_connection):
    """Mock ConnectionManager with proper connection behavior."""
    manager = Mock(spec=ConnectionManager)
    manager.connections = {"indices": mock_websocket_connection}

    # Mock get_connection to return mock connection
    manager.get_connection = Mock(return_value=mock_websocket_connection)

    return manager


@pytest.fixture
def mcp_server(mock_connection_manager):
    """FastMCP instance with indices tools registered."""
    mcp = FastMCP("test-indices")
    indices.register_tools(mcp, mock_connection_manager)
    return mcp


# ============================================================================
# start_indices_stream Tests (4 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_start_indices_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful indices stream start with valid API key."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool(
        "start_indices_stream",
        {
            "channels": ["V.I:SPX", "AM.I:DJI"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Started indices WebSocket stream" in result_text
    assert "V.I:SPX, AM.I:DJI" in result_text

    # Verify connection manager called correctly
    mock_connection_manager.get_connection.assert_called_once_with(
        "indices",
        endpoint="wss://socket.polygon.io/indices",
        api_key="test_api_key"
    )

    # Verify connection methods called
    mock_websocket_connection.connect.assert_awaited_once()
    mock_websocket_connection.subscribe.assert_awaited_once_with(["V.I:SPX", "AM.I:DJI"])


@pytest.mark.asyncio
async def test_start_indices_stream_with_custom_endpoint(mock_connection_manager, mock_websocket_connection):
    """Test stream start with custom delayed endpoint."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)
    custom_endpoint = "wss://delayed.polygon.io/indices"

    # Act
    result = await mcp.call_tool(
        "start_indices_stream",
        {
            "channels": ["V.I:SPX"],
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
        "indices",
        endpoint=custom_endpoint,
        api_key="test_api_key"
    )


@pytest.mark.asyncio
async def test_start_indices_stream_uses_env_api_key(mock_connection_manager, mock_websocket_connection):
    """Test stream start uses POLYGON_API_KEY environment variable when not provided."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    with patch.dict(os.environ, {"POLYGON_API_KEY": "env_api_key"}):
        # Act
        result = await mcp.call_tool(
            "start_indices_stream",
            {"channels": ["V.I:SPX"]}
        )

    # Assert
    result_text = str(result)
    assert "✓" in result_text

    # Verify env API key used
    mock_connection_manager.get_connection.assert_called_once_with(
        "indices",
        endpoint="wss://socket.polygon.io/indices",
        api_key="env_api_key"
    )


@pytest.mark.asyncio
async def test_start_indices_stream_connection_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when connection fails."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock connection failure
    mock_websocket_connection.connect.side_effect = Exception("Connection timeout")

    # Act
    result = await mcp.call_tool(
        "start_indices_stream",
        {
            "channels": ["V.I:SPX"],
            "api_key": "test_api_key"
        }
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to start indices stream" in result_text
    assert "Connection timeout" in result_text


# ============================================================================
# stop_indices_stream Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_stop_indices_stream_success(mock_connection_manager, mock_websocket_connection):
    """Test successful stop of active stream."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("stop_indices_stream", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Stopped indices WebSocket stream" in result_text

    # Verify connection closed
    mock_connection_manager.get_connection.assert_called_once_with("indices")
    mock_websocket_connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_indices_stream_no_active_connection(mock_connection_manager):
    """Test stop when no stream exists (KeyError handling)."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("indices")

    # Act
    result = await mcp.call_tool("stop_indices_stream", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active indices WebSocket connection" in result_text


# ============================================================================
# get_indices_stream_status Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_get_indices_stream_status_active(mock_connection_manager, mock_websocket_connection):
    """Test status retrieval for active connection."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("get_indices_stream_status", {})

    # Assert
    result_text = str(result)
    assert "✓" in result_text or "INDICES" in result_text
    assert "connected" in result_text.lower()
    assert "wss://socket.polygon.io/indices" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_get_indices_stream_status_no_connection(mock_connection_manager):
    """Test status when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("indices")

    # Act
    result = await mcp.call_tool("get_indices_stream_status", {})

    # Assert
    result_text = str(result)
    assert "○" in result_text
    assert "No active indices WebSocket connection" in result_text


# ============================================================================
# subscribe_indices_channels Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_subscribe_indices_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful subscription to new channels."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)
    new_channels = ["V.I:NDX", "AM.I:RUT"]

    # Act
    result = await mcp.call_tool(
        "subscribe_indices_channels",
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
async def test_subscribe_indices_channels_no_stream(mock_connection_manager):
    """Test subscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("indices")

    # Act
    result = await mcp.call_tool(
        "subscribe_indices_channels",
        {"channels": ["V.I:SPX"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active indices stream" in result_text
    assert "Use start_indices_stream() first" in result_text


@pytest.mark.asyncio
async def test_subscribe_indices_channels_failure(mock_connection_manager, mock_websocket_connection):
    """Test error handling when subscription fails."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock subscription failure
    mock_websocket_connection.subscribe.side_effect = Exception("Invalid channel format")

    # Act
    result = await mcp.call_tool(
        "subscribe_indices_channels",
        {"channels": ["INVALID"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "Failed to subscribe" in result_text
    assert "Invalid channel format" in result_text


# ============================================================================
# unsubscribe_indices_channels Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_unsubscribe_indices_channels_success(mock_connection_manager, mock_websocket_connection):
    """Test successful unsubscription from channels."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Update mock status after unsubscribe
    mock_websocket_connection.get_status.return_value = {
        "market": "indices",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/indices",
        "subscriptions": ["AM.I:DJI"],  # Only one remaining
        "subscription_count": 1,
    }

    # Act
    result = await mcp.call_tool(
        "unsubscribe_indices_channels",
        {"channels": ["V.I:SPX"]}
    )

    # Assert
    result_text = str(result)
    assert "✓" in result_text
    assert "Removed 1 subscriptions" in result_text
    assert "Total subscriptions: 1" in result_text

    # Verify unsubscribe called
    mock_websocket_connection.unsubscribe.assert_awaited_once_with(["V.I:SPX"])
    mock_websocket_connection.get_status.assert_called()


@pytest.mark.asyncio
async def test_unsubscribe_indices_channels_no_stream(mock_connection_manager):
    """Test unsubscribe when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("indices")

    # Act
    result = await mcp.call_tool(
        "unsubscribe_indices_channels",
        {"channels": ["V.I:SPX"]}
    )

    # Assert
    result_text = str(result)
    assert "✗" in result_text
    assert "No active indices stream" in result_text
    assert "Use start_indices_stream() first" in result_text


# ============================================================================
# list_indices_subscriptions Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_list_indices_subscriptions_active(mock_connection_manager, mock_websocket_connection):
    """Test listing subscriptions for active stream."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Act
    result = await mcp.call_tool("list_indices_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Indices Stream Subscriptions" in result_text
    assert "2 total" in result_text
    assert "V.I:SPX" in result_text or "AM.I:DJI" in result_text

    # Verify get_status called
    mock_websocket_connection.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_list_indices_subscriptions_grouped_by_type(mock_connection_manager, mock_websocket_connection):
    """Test subscriptions are grouped by channel type (3 groups: V.I:, AM.I:, AS.I:)."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Update mock with multiple channel types (unique to indices: V, AM, AS)
    mock_websocket_connection.get_status.return_value = {
        "market": "indices",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/indices",
        "subscriptions": [
            "V.I:SPX", "V.I:DJI",  # Values
            "AM.I:SPX",             # Minute agg
            "AS.I:SPX"              # Second agg
        ],
        "subscription_count": 4,
    }

    # Act
    result = await mcp.call_tool("list_indices_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "Values" in result_text
    assert "Minute Aggregates" in result_text
    assert "Second Aggregates" in result_text


@pytest.mark.asyncio
async def test_list_indices_subscriptions_empty(mock_connection_manager, mock_websocket_connection):
    """Test listing when no subscriptions exist."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Update mock with no subscriptions
    mock_websocket_connection.get_status.return_value = {
        "market": "indices",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/indices",
        "subscriptions": [],
        "subscription_count": 0,
    }

    # Act
    result = await mcp.call_tool("list_indices_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active subscriptions" in result_text


@pytest.mark.asyncio
async def test_list_indices_subscriptions_no_connection(mock_connection_manager):
    """Test list when no stream exists."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Mock KeyError when getting connection
    mock_connection_manager.get_connection.side_effect = KeyError("indices")

    # Act
    result = await mcp.call_tool("list_indices_subscriptions", {})

    # Assert
    result_text = str(result)
    assert "No active indices WebSocket connection" in result_text


# ============================================================================
# Integration Tests (2 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_complete_workflow_start_subscribe_stop(mock_connection_manager, mock_websocket_connection):
    """Test complete workflow: start -> subscribe -> stop."""
    # Arrange
    mcp = FastMCP("test")
    indices.register_tools(mcp, mock_connection_manager)

    # Act & Assert - Start
    result1 = await mcp.call_tool(
        "start_indices_stream",
        {
            "channels": ["V.I:SPX"],
            "api_key": "test_api_key"
        }
    )
    result1_text = str(result1)
    assert "✓" in result1_text
    assert "Started indices WebSocket stream" in result1_text

    # Act & Assert - Subscribe
    mock_websocket_connection.subscribe.reset_mock()
    result2 = await mcp.call_tool(
        "subscribe_indices_channels",
        {"channels": ["AM.I:SPX"]}
    )
    result2_text = str(result2)
    assert "✓" in result2_text
    assert "Added 1 subscriptions" in result2_text

    # Act & Assert - Stop
    result3 = await mcp.call_tool("stop_indices_stream", {})
    result3_text = str(result3)
    assert "✓" in result3_text
    assert "Stopped indices WebSocket stream" in result3_text

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
    indices.register_tools(mcp, mock_connection_manager)

    # Assert - Verify all tools registered
    tool_names = [tool.name for tool in mcp._tool_manager._tools.values()]

    expected_tools = [
        "start_indices_stream",
        "stop_indices_stream",
        "get_indices_stream_status",
        "subscribe_indices_channels",
        "unsubscribe_indices_channels",
        "list_indices_subscriptions",
    ]

    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Tool {tool_name} not registered"
