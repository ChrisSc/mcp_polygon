"""
Unit tests for WebSocket stream message formatting.

Tests all message formatting functions including:
- Trade, quote, aggregate, index, LULD, and FMV message formatting
- Status message formatting
- Connection status formatting
- Edge cases (missing fields, empty data, special characters)
- Pretty printing vs compact JSON
"""

import json
import pytest

from mcp_polygon.tools.websockets.stream_formatter import (
    format_stream_message,
    format_status_message,
    format_connection_status,
)


# ============================================================================
# Fixtures - Sample Data
# ============================================================================


@pytest.fixture
def sample_trade():
    """Sample trade message."""
    return {
        "ev": "T",
        "sym": "AAPL",
        "p": 150.25,
        "s": 100,
        "x": 4,
        "c": [0, 12],
        "t": 1640995200000,
    }


@pytest.fixture
def sample_quote():
    """Sample quote message."""
    return {
        "ev": "Q",
        "sym": "MSFT",
        "bp": 300.50,
        "ap": 300.75,
        "bs": 200,
        "as": 150,
        "bx": 4,
        "ax": 8,
        "t": 1640995200000,
    }


@pytest.fixture
def sample_minute_aggregate():
    """Sample minute aggregate message."""
    return {
        "ev": "AM",
        "sym": "GOOGL",
        "o": 2800.00,
        "h": 2825.50,
        "l": 2795.25,
        "c": 2820.75,
        "v": 50000,
        "av": 1500000,
        "vw": 2810.25,
        "s": 1640995200000,
        "e": 1640995260000,
    }


@pytest.fixture
def sample_second_aggregate():
    """Sample second aggregate message."""
    return {
        "ev": "A",
        "sym": "TSLA",
        "o": 1000.00,
        "h": 1005.00,
        "l": 998.50,
        "c": 1002.25,
        "v": 1000,
        "s": 1640995200000,
        "e": 1640995201000,
    }


@pytest.fixture
def sample_index_value():
    """Sample index value message."""
    return {"ev": "V", "sym": "I:SPX", "val": 4500.25, "t": 1640995200000}


@pytest.fixture
def sample_luld():
    """Sample LULD (Limit Up Limit Down) message."""
    return {"ev": "LULD", "sym": "GME", "tier": 1, "halt": True, "t": 1640995200000}


@pytest.fixture
def sample_fmv():
    """Sample Fair Market Value message."""
    return {
        "ev": "FMV",
        "sym": "O:SPY251219C00650000",
        "fmv": 15.50,
        "t": 1640995200000,
    }


# ============================================================================
# Trade Message Formatting Tests (4 tests)
# ============================================================================


def test_format_trade_complete(sample_trade):
    """Test formatting trade message with all fields."""
    result = format_stream_message(sample_trade, pretty=False)
    data = json.loads(result)

    assert data["event"] == "TRADE"
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.25
    assert data["size"] == 100
    assert data["exchange_id"] == 4
    assert data["conditions"] == [0, 12]
    assert "timestamp" in data
    assert data["full_data"]["ev"] == "T"


def test_format_trade_with_timestamp():
    """Test trade message includes readable timestamp."""
    trade = {"ev": "T", "sym": "AAPL", "p": 150.25, "s": 100, "t": 1640995200000}

    result = format_stream_message(trade, pretty=False)
    data = json.loads(result)

    # Check timestamp was converted
    assert "timestamp_readable" in data["full_data"]
    assert data["timestamp"] is not None


def test_format_trade_missing_optional_fields():
    """Test trade formatting with missing optional fields."""
    trade = {"ev": "T", "sym": "AAPL", "p": 150.25, "s": 100, "t": 1640995200000}

    result = format_stream_message(trade, pretty=False)
    data = json.loads(result)

    assert data["event"] == "TRADE"
    assert data["symbol"] == "AAPL"
    assert data["exchange_id"] is None
    assert data["conditions"] == []  # Default empty list


def test_format_trade_pretty_printing(sample_trade):
    """Test trade formatting with pretty printing."""
    result = format_stream_message(sample_trade, pretty=True)

    # Pretty printed JSON should have newlines and indentation
    assert "\n" in result
    assert "  " in result

    # Should still be valid JSON
    data = json.loads(result)
    assert data["event"] == "TRADE"


# ============================================================================
# Quote Message Formatting Tests (5 tests)
# ============================================================================


def test_format_quote_complete(sample_quote):
    """Test formatting quote message with all fields."""
    result = format_stream_message(sample_quote, pretty=False)
    data = json.loads(result)

    assert data["event"] == "QUOTE"
    assert data["symbol"] == "MSFT"
    assert data["bid"]["price"] == 300.50
    assert data["bid"]["size"] == 200
    assert data["bid"]["exchange"] == 4
    assert data["ask"]["price"] == 300.75
    assert data["ask"]["size"] == 150
    assert data["ask"]["exchange"] == 8
    assert data["spread"] == 0.25  # 300.75 - 300.50


def test_format_quote_spread_calculation():
    """Test quote spread calculation."""
    quote = {"ev": "Q", "sym": "AAPL", "bp": 150.00, "ap": 150.10, "t": 1640995200000}

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["spread"] == 0.1  # Rounded to 4 decimals


def test_format_quote_wide_spread():
    """Test quote with wide spread."""
    quote = {"ev": "Q", "sym": "TSLA", "bp": 1000.00, "ap": 1005.50, "t": 1640995200000}

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["spread"] == 5.5


def test_format_quote_missing_optional_fields():
    """Test quote formatting with missing optional fields."""
    quote = {"ev": "Q", "sym": "AAPL", "bp": 150.00, "ap": 150.10, "t": 1640995200000}

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["event"] == "QUOTE"
    assert data["bid"]["size"] is None
    assert data["bid"]["exchange"] is None
    assert data["ask"]["size"] is None
    assert data["ask"]["exchange"] is None


def test_format_quote_zero_spread():
    """Test quote with zero spread (locked market)."""
    quote = {"ev": "Q", "sym": "AAPL", "bp": 150.00, "ap": 150.00, "t": 1640995200000}

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["spread"] == 0.0


# ============================================================================
# Aggregate Message Formatting Tests (6 tests)
# ============================================================================


def test_format_minute_aggregate(sample_minute_aggregate):
    """Test formatting minute aggregate message."""
    result = format_stream_message(sample_minute_aggregate, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_MINUTE"
    assert data["symbol"] == "GOOGL"
    assert data["open"] == 2800.00
    assert data["high"] == 2825.50
    assert data["low"] == 2795.25
    assert data["close"] == 2820.75
    assert data["volume"] == 50000
    assert data["accumulated_volume"] == 1500000
    assert data["vwap"] == 2810.25


def test_format_second_aggregate(sample_second_aggregate):
    """Test formatting second aggregate message."""
    result = format_stream_message(sample_second_aggregate, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_SECOND"
    assert data["symbol"] == "TSLA"
    assert data["open"] == 1000.00
    assert data["high"] == 1005.00
    assert data["low"] == 998.50
    assert data["close"] == 1002.25


def test_format_aggregate_with_time_range(sample_minute_aggregate):
    """Test aggregate includes start and end times."""
    result = format_stream_message(sample_minute_aggregate, pretty=False)
    data = json.loads(result)

    assert data["start_time"] == 1640995200000
    assert data["end_time"] == 1640995260000


def test_format_aggregate_crypto():
    """Test formatting crypto aggregate (XA event type)."""
    agg = {
        "ev": "XA",
        "sym": "BTC-USD",
        "o": 50000.00,
        "h": 50500.00,
        "l": 49800.00,
        "c": 50200.00,
        "v": 100,
        "t": 1640995200000,
    }

    result = format_stream_message(agg, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_MINUTE"
    assert data["symbol"] == "BTC-USD"


def test_format_aggregate_forex():
    """Test formatting forex aggregate (CA event type)."""
    agg = {
        "ev": "CA",
        "sym": "EUR/USD",
        "o": 1.1000,
        "h": 1.1050,
        "l": 1.0990,
        "c": 1.1020,
        "t": 1640995200000,
    }

    result = format_stream_message(agg, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_MINUTE"
    assert data["symbol"] == "EUR/USD"


def test_format_aggregate_missing_optional_fields():
    """Test aggregate with missing optional fields."""
    agg = {"ev": "AM", "sym": "AAPL", "o": 150.00, "c": 151.00, "t": 1640995200000}

    result = format_stream_message(agg, pretty=False)
    data = json.loads(result)

    assert data["event"] == "AGGREGATE_MINUTE"
    assert data["high"] is None
    assert data["low"] is None
    assert data["volume"] is None


# ============================================================================
# Index Value Message Formatting Tests (2 tests)
# ============================================================================


def test_format_index_value(sample_index_value):
    """Test formatting index value message."""
    result = format_stream_message(sample_index_value, pretty=False)
    data = json.loads(result)

    assert data["event"] == "INDEX_VALUE"
    assert data["symbol"] == "I:SPX"
    assert data["value"] == 4500.25
    assert "timestamp" in data


def test_format_index_value_missing_fields():
    """Test index value with missing fields."""
    index = {"ev": "V", "t": 1640995200000}

    result = format_stream_message(index, pretty=False)
    data = json.loads(result)

    assert data["event"] == "INDEX_VALUE"
    assert data["symbol"] is None
    assert data["value"] is None


# ============================================================================
# LULD Message Formatting Tests (2 tests)
# ============================================================================


def test_format_luld(sample_luld):
    """Test formatting LULD message."""
    result = format_stream_message(sample_luld, pretty=False)
    data = json.loads(result)

    assert data["event"] == "LULD"
    assert data["symbol"] == "GME"
    assert data["tier"] == 1
    assert data["halt"] is True
    assert "timestamp" in data


def test_format_luld_no_halt():
    """Test LULD message with halt=False."""
    luld = {"ev": "LULD", "sym": "AMC", "tier": 2, "halt": False, "t": 1640995200000}

    result = format_stream_message(luld, pretty=False)
    data = json.loads(result)

    assert data["event"] == "LULD"
    assert data["halt"] is False


# ============================================================================
# FMV Message Formatting Tests (2 tests)
# ============================================================================


def test_format_fmv(sample_fmv):
    """Test formatting Fair Market Value message."""
    result = format_stream_message(sample_fmv, pretty=False)
    data = json.loads(result)

    assert data["event"] == "FAIR_MARKET_VALUE"
    assert data["symbol"] == "O:SPY251219C00650000"
    assert data["fair_value"] == 15.50
    assert "timestamp" in data


def test_format_fmv_zero_value():
    """Test FMV with zero fair value."""
    fmv = {"ev": "FMV", "sym": "O:TEST", "fmv": 0.0, "t": 1640995200000}

    result = format_stream_message(fmv, pretty=False)
    data = json.loads(result)

    assert data["event"] == "FAIR_MARKET_VALUE"
    assert data["fair_value"] == 0.0


# ============================================================================
# Unknown Event Type Tests (2 tests)
# ============================================================================


def test_format_unknown_event_type():
    """Test formatting unknown event type falls back to generic."""
    message = {"ev": "UNKNOWN_TYPE", "data": "test", "t": 1640995200000}

    result = format_stream_message(message, pretty=False)
    data = json.loads(result)

    # Should preserve original data
    assert data["ev"] == "UNKNOWN_TYPE"
    assert data["data"] == "test"
    assert "timestamp_readable" in data


def test_format_message_without_event_type():
    """Test formatting message without event type."""
    message = {"data": "test", "value": 123}

    result = format_stream_message(message, pretty=False)
    data = json.loads(result)

    # Should preserve all data
    assert data["data"] == "test"
    assert data["value"] == 123


# ============================================================================
# Status Message Formatting Tests (6 tests)
# ============================================================================


def test_format_status_connected():
    """Test formatting connected status."""
    status = {"status": "connected", "message": "WebSocket ready"}
    result = format_status_message(status)

    assert result == "✓ Connected to Polygon WebSocket: WebSocket ready"


def test_format_status_auth_success():
    """Test formatting auth success status."""
    status = {"status": "auth_success", "message": "Authentication successful"}
    result = format_status_message(status)

    assert result == "✓ Authenticated successfully: Authentication successful"


def test_format_status_auth_failed():
    """Test formatting auth failed status."""
    status = {"status": "auth_failed", "message": "Invalid API key"}
    result = format_status_message(status)

    assert result == "✗ Authentication failed: Invalid API key"


def test_format_status_success():
    """Test formatting generic success status."""
    status = {"status": "success", "message": "Subscribed to channels"}
    result = format_status_message(status)

    assert result == "✓ Success: Subscribed to channels"


def test_format_status_error():
    """Test formatting error status."""
    status = {"status": "error", "message": "Connection timeout"}
    result = format_status_message(status)

    assert result == "✗ Error: Connection timeout"


def test_format_status_unknown():
    """Test formatting unknown status type."""
    status = {"status": "custom_type", "message": "Custom message"}
    result = format_status_message(status)

    assert result == "[CUSTOM_TYPE] Custom message"


# ============================================================================
# Connection Status Formatting Tests (6 tests)
# ============================================================================


def test_format_connection_status_connected():
    """Test formatting connected connection status."""
    status = {
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": ["T.AAPL", "Q.MSFT"],
        "subscription_count": 2,
    }

    result = format_connection_status(status)

    assert "✓" in result
    assert "STOCKS WebSocket" in result
    assert "State: connected" in result
    assert "Subscriptions: 2 channels" in result
    assert "T.AAPL" in result
    assert "Q.MSFT" in result


def test_format_connection_status_connecting():
    """Test formatting connecting state."""
    status = {
        "market": "crypto",
        "state": "connecting",
        "endpoint": "wss://socket.polygon.io/crypto",
        "subscriptions": [],
        "subscription_count": 0,
    }

    result = format_connection_status(status)

    assert "⟳" in result
    assert "CRYPTO WebSocket" in result
    assert "State: connecting" in result


def test_format_connection_status_authenticating():
    """Test formatting authenticating state."""
    status = {
        "market": "forex",
        "state": "authenticating",
        "endpoint": "wss://socket.polygon.io/forex",
        "subscriptions": [],
        "subscription_count": 0,
    }

    result = format_connection_status(status)

    assert "🔐" in result
    assert "State: authenticating" in result


def test_format_connection_status_disconnected():
    """Test formatting disconnected state."""
    status = {
        "market": "options",
        "state": "disconnected",
        "endpoint": "wss://socket.polygon.io/options",
        "subscriptions": [],
        "subscription_count": 0,
    }

    result = format_connection_status(status)

    assert "○" in result
    assert "State: disconnected" in result


def test_format_connection_status_error():
    """Test formatting error state."""
    status = {
        "market": "futures",
        "state": "error",
        "endpoint": "wss://socket.polygon.io/futures",
        "subscriptions": ["GC.FUT"],
        "subscription_count": 1,
    }

    result = format_connection_status(status)

    assert "✗" in result
    assert "State: error" in result


def test_format_connection_status_many_subscriptions():
    """Test formatting with many subscriptions (truncation)."""
    status = {
        "market": "stocks",
        "state": "connected",
        "endpoint": "wss://socket.polygon.io/stocks",
        "subscriptions": [
            "T.AAPL",
            "T.MSFT",
            "T.GOOGL",
            "T.TSLA",
            "T.AMZN",
            "T.NVDA",
            "T.META",
        ],
        "subscription_count": 7,
    }

    result = format_connection_status(status)

    assert "Subscriptions: 7 channels" in result
    assert "..." in result  # Should show ellipsis for truncated list
    assert "T.AAPL" in result  # First 5 should be shown


# ============================================================================
# Edge Cases and Special Scenarios (5 tests)
# ============================================================================


def test_timestamp_conversion_accuracy():
    """Test timestamp conversion is accurate."""
    message = {
        "ev": "T",
        "sym": "AAPL",
        "p": 150.00,
        "s": 100,
        "t": 1640995200000,  # 2022-01-01 00:00:00 UTC
    }

    result = format_stream_message(message, pretty=False)
    data = json.loads(result)

    # Verify timestamp was added
    assert "timestamp_readable" in data["full_data"]

    # Should be ISO format
    timestamp = data["full_data"]["timestamp_readable"]
    assert "T" in timestamp or " " in timestamp  # ISO format contains T or space


def test_empty_conditions_array():
    """Test trade with empty conditions array."""
    trade = {
        "ev": "T",
        "sym": "AAPL",
        "p": 150.00,
        "s": 100,
        "c": [],
        "t": 1640995200000,
    }

    result = format_stream_message(trade, pretty=False)
    data = json.loads(result)

    assert data["conditions"] == []


def test_zero_prices_and_sizes():
    """Test handling of zero values in prices/sizes."""
    quote = {
        "ev": "Q",
        "sym": "TEST",
        "bp": 0.0,
        "ap": 0.0,
        "bs": 0,
        "as": 0,
        "t": 1640995200000,
    }

    result = format_stream_message(quote, pretty=False)
    data = json.loads(result)

    assert data["bid"]["price"] == 0.0
    assert data["ask"]["price"] == 0.0
    assert data["spread"] == 0.0


def test_missing_timestamp_field():
    """Test message without timestamp field."""
    message = {"ev": "T", "sym": "AAPL", "p": 150.00, "s": 100}

    result = format_stream_message(message, pretty=False)
    data = json.loads(result)

    # Should not have timestamp_readable
    assert "timestamp_readable" not in data["full_data"]
    assert data["timestamp"] is None


def test_compact_json_output():
    """Test compact JSON output (pretty=False)."""
    message = {"ev": "T", "sym": "AAPL", "p": 150.00, "s": 100, "t": 1640995200000}

    result = format_stream_message(message, pretty=False)

    # Compact JSON should not have indentation
    assert result.count("\n") <= 1  # May have trailing newline
    assert "  " not in result  # No double-space indentation
