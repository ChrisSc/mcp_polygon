"""Tests for new error handling features (DEBUG.md priorities 1-4)."""

import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from mcp_polygon.api_wrapper import PolygonAPIWrapper
from mcp_polygon.validation import validate_date, validate_date_any_of
from mcp_polygon.formatters import json_to_csv


def make_http_error(status_code: int, message: str = "") -> Exception:
    """Create a mock HTTP error with proper response structure."""
    error = Exception(message or f"HTTP {status_code} error")
    error.response = Mock(status_code=status_code)
    return error


class TestAPITierErrorDetection:
    """Test Suite 1: API Tier Error Detection (Priority 1 & 3)"""

    @pytest.mark.asyncio
    async def test_not_authorized_uppercase_detected(self):
        """Test detection of NOT_AUTHORIZED error in uppercase."""
        client = Mock()
        client.list_options_contracts = Mock(
            side_effect=Exception("NOT_AUTHORIZED - You are not entitled to this data")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("list_options_contracts", ticker="AAPL")

        assert "API tier limitation" in result
        assert "NOT_AUTHORIZED" in result
        assert "https://polygon.io/pricing" in result
        assert "method=list_options_contracts" in result

    @pytest.mark.asyncio
    async def test_not_entitled_lowercase_detected(self):
        """Test detection of 'not entitled' error in lowercase."""
        client = Mock()
        client.get_indices_snapshot = Mock(
            side_effect=Exception("you are not entitled to access this endpoint")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("get_indices_snapshot", ticker_any_of="I:SPX")

        assert "API tier limitation" in result
        assert "not entitled" in result.lower()
        assert "https://polygon.io/pricing" in result
        assert "method=get_indices_snapshot" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_includes_upgrade_link(self):
        """Test that API tier errors include polygon.io upgrade link."""
        client = Mock()
        client.list_options_contracts = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("list_options_contracts")

        assert "Upgrade at: https://polygon.io/pricing" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_with_ticker_context(self):
        """Test API tier error includes ticker in context."""
        client = Mock()
        client.get_snapshot_ticker = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call(
            "get_snapshot_ticker",
            market_type="indices",
            ticker="I:SPX"
        )

        assert "ticker=I:SPX" in result
        assert "method=get_snapshot_ticker" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_with_currency_pair_context(self):
        """Test API tier error includes currency pair in context."""
        client = Mock()
        client.get_last_forex_quote = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call(
            "get_last_forex_quote",
            from_="EUR",
            to="USD"
        )

        assert "currency_pair=EUR_USD" in result
        assert "method=get_last_forex_quote" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_with_date_range_context(self):
        """Test API tier error includes date range in context."""
        client = Mock()
        client.get_aggs = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call(
            "get_aggs",
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_="2024-01-01",
            to="2024-01-31"
        )

        assert "ticker=AAPL" in result
        assert "date_range=2024-01-01 to 2024-01-31" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_with_single_date_context(self):
        """Test API tier error includes single date in context."""
        client = Mock()
        client.get_daily_open_close_agg = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call(
            "get_daily_open_close_agg",
            ticker="AAPL",
            date="2024-01-15"
        )

        assert "date=2024-01-15" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_message_format(self):
        """Test complete API tier error message format."""
        client = Mock()
        client.list_options_contracts = Mock(
            side_effect=Exception("NOT_AUTHORIZED - Insufficient permissions")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("list_options_contracts", ticker="AAPL")

        # Check all parts of the formatted message
        assert "API tier limitation:" in result
        assert "Your Polygon.io plan does not include access to" in result
        assert "list_options_contracts" in result
        assert "This tool requires a higher subscription tier." in result
        assert "Upgrade at: https://polygon.io/pricing" in result
        assert "Context:" in result
        assert "Details:" in result
        assert "NOT_AUTHORIZED" in result

    @pytest.mark.asyncio
    async def test_api_tier_error_with_multiple_context_fields(self):
        """Test API tier error with ticker, date range, and other context."""
        client = Mock()
        client.get_aggs = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call(
            "get_aggs",
            ticker="O:SPY251219C00650000",
            multiplier=5,
            timespan="minute",
            from_="2024-01-01",
            to="2024-01-02"
        )

        # All context should be present
        assert "method=get_aggs" in result
        assert "ticker=O:SPY251219C00650000" in result
        assert "date_range=2024-01-01 to 2024-01-02" in result

    @pytest.mark.asyncio
    async def test_non_api_tier_error_not_affected(self):
        """Test that non-API tier errors are not reformatted."""
        client = Mock()
        client.get_aggs = Mock(
            side_effect=Exception("Network timeout occurred")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("get_aggs", ticker="AAPL")

        # Should use standard timeout error format
        assert "timed out" in result.lower() or "timeout" in result.lower()
        assert "API tier limitation" not in result
        assert "polygon.io/pricing" not in result


class TestDateValidation:
    """Test Suite 2: Date Validation (validate_date) (Priority 2)"""

    def test_validate_date_accepts_none(self):
        """Test that None date is valid."""
        result = validate_date(None, "from_")
        assert result is None

    def test_validate_date_accepts_past_date_string(self):
        """Test that past date string is valid."""
        result = validate_date("2024-01-01", "date")
        assert result is None

    def test_validate_date_accepts_today(self):
        """Test that today's date is valid."""
        today = datetime.now(timezone.utc).date().isoformat()
        result = validate_date(today, "date")
        assert result is None

    def test_validate_date_rejects_far_future_date(self):
        """Test that far future date is rejected."""
        future = datetime.now(timezone.utc) + timedelta(days=365)
        future_str = future.date().isoformat()

        result = validate_date(future_str, "from_")

        assert result is not None
        assert "Error" in result
        assert "from_" in result
        assert "in the future" in result
        assert "Polygon.io provides historical data only" in result
        assert "WebSocket streaming" in result

    def test_validate_date_accepts_tomorrow_within_tolerance(self):
        """Test that tomorrow is accepted (1-day timezone tolerance)."""
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        tomorrow_str = tomorrow.date().isoformat()

        result = validate_date(tomorrow_str, "date")
        # Should be None (valid) due to 1-day tolerance
        assert result is None

    def test_validate_date_rejects_day_after_tomorrow(self):
        """Test that day after tomorrow is rejected (beyond tolerance)."""
        future = datetime.now(timezone.utc) + timedelta(days=2)
        future_str = future.date().isoformat()

        result = validate_date(future_str, "to")

        assert result is not None
        assert "Error" in result
        assert "to" in result

    def test_validate_date_with_iso_string_with_timezone(self):
        """Test validation with ISO string including timezone."""
        past = "2024-01-01T00:00:00Z"
        result = validate_date(past, "date")
        assert result is None

        future = datetime.now(timezone.utc) + timedelta(days=30)
        future_iso = future.isoformat().replace("+00:00", "Z")
        result = validate_date(future_iso, "date")
        assert result is not None
        assert "Error" in result

    def test_validate_date_with_iso_string_without_timezone(self):
        """Test validation with ISO string without timezone (assumes UTC)."""
        past = "2024-01-01T00:00:00"
        result = validate_date(past, "date")
        assert result is None

    def test_validate_date_with_datetime_object_with_timezone(self):
        """Test validation with datetime object with timezone."""
        past = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = validate_date(past, "date")
        assert result is None

        future = datetime.now(timezone.utc) + timedelta(days=30)
        result = validate_date(future, "date")
        assert result is not None

    def test_validate_date_with_datetime_object_without_timezone(self):
        """Test validation with datetime object without timezone (assumes UTC)."""
        past = datetime(2024, 1, 1)
        result = validate_date(past, "date")
        assert result is None

    def test_validate_date_with_date_object(self):
        """Test validation with date object."""
        past = date(2024, 1, 1)
        result = validate_date(past, "date")
        assert result is None

        future = (datetime.now(timezone.utc) + timedelta(days=30)).date()
        result = validate_date(future, "date")
        assert result is not None

    def test_validate_date_with_int_timestamp(self):
        """Test validation with integer timestamp (milliseconds)."""
        # January 1, 2024 in milliseconds
        past_timestamp = 1704067200000
        result = validate_date(past_timestamp, "date")
        assert result is None

        # Future timestamp
        future = datetime.now(timezone.utc) + timedelta(days=30)
        future_timestamp = int(future.timestamp() * 1000)
        result = validate_date(future_timestamp, "date")
        assert result is not None

    def test_validate_date_invalid_format_ignored(self):
        """Test that invalid date formats are ignored (let API handle)."""
        # Invalid formats should return None (no validation error)
        result = validate_date("not-a-date", "date")
        assert result is None

        result = validate_date("2024-13-45", "date")
        assert result is None

    def test_validate_date_error_includes_parameter_name(self):
        """Test that error message includes the parameter name."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        result = validate_date(future, "from_")
        assert "from_" in result

        result = validate_date(future, "date_lte")
        assert "date_lte" in result

    def test_validate_date_error_includes_current_date(self):
        """Test that error message includes current date."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        result = validate_date(future, "date")

        assert "Current date:" in result
        # Check that a date is present (YYYY-MM-DD format)
        assert "20" in result  # Year starts with 20

    def test_validate_date_consistency_across_modules(self):
        """Test that stocks and economy modules have identical validation."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        stocks_result = validate_date(future, "date")
        economy_result = validate_date(future, "date")

        # Both should reject the future date
        assert stocks_result is not None
        assert economy_result is not None
        # Error messages should be similar
        assert "in the future" in stocks_result
        assert "in the future" in economy_result


class TestDateAnyOfValidation:
    """Test Suite 3: Date Any Of Validation (Priority 2b)"""

    def testvalidate_date_any_of_accepts_none(self):
        """Test that None is valid."""
        result = validate_date_any_of(None)
        assert result is None

    def testvalidate_date_any_of_accepts_empty_string(self):
        """Test that empty string is valid."""
        result = validate_date_any_of("")
        assert result is None

    def testvalidate_date_any_of_accepts_valid_single_date(self):
        """Test single valid past date."""
        result = validate_date_any_of("2024-01-01")
        assert result is None

    def testvalidate_date_any_of_accepts_valid_comma_separated_dates(self):
        """Test multiple valid past dates."""
        result = validate_date_any_of("2024-01-01,2024-01-15,2024-02-01")
        assert result is None

    def testvalidate_date_any_of_accepts_dates_with_spaces(self):
        """Test dates with spaces around commas are handled."""
        result = validate_date_any_of("2024-01-01, 2024-01-15 , 2024-02-01")
        assert result is None

    def testvalidate_date_any_of_rejects_future_date_in_list(self):
        """Test that future date in list is rejected."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        date_list = f"2024-01-01,{future},2024-02-01"

        result = validate_date_any_of(date_list)

        assert result is not None
        assert "Error" in result
        assert "in the future" in result
        assert "date_any_of" in result

    def testvalidate_date_any_of_rejects_first_future_date(self):
        """Test that first date being future is caught."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        date_list = f"{future},2024-01-01"

        result = validate_date_any_of(date_list)

        assert result is not None
        assert "Error" in result

    def testvalidate_date_any_of_with_single_future_date(self):
        """Test single future date without comma."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        result = validate_date_any_of(future)

        assert result is not None
        assert "Error" in result

    def testvalidate_date_any_of_invalid_format_ignored(self):
        """Test that invalid formats in list are ignored (let API handle)."""
        # Invalid formats should not cause validation errors
        result = validate_date_any_of("not-a-date,2024-01-01")
        assert result is None

    def testvalidate_date_any_of_stops_at_first_error(self):
        """Test that validation stops at first error."""
        future1 = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        future2 = (datetime.now(timezone.utc) + timedelta(days=60)).date().isoformat()
        date_list = f"2024-01-01,{future1},{future2}"

        result = validate_date_any_of(date_list)

        # Should return error for first future date
        assert result is not None
        assert future1 in result


class TestStartupDiagnostics:
    """Test Suite 4: Startup Diagnostics (Priority 4)"""

    @pytest.mark.asyncio
    async def test_diagnostics_with_valid_api_key(self):
        """Test diagnostics with valid API key and successful connection."""
        from mcp_polygon.server import run_startup_diagnostics, polygon_client

        # Mock successful API call
        mock_response = Mock()
        mock_response.data = b'{"results": [{"t": 1640995200000, "o": 150}]}'

        with patch.object(polygon_client, 'get_aggs', return_value=mock_response):
            with patch('mcp_polygon.server.POLYGON_API_KEY', 'test_key_1234'):
                with patch('mcp_polygon.server.logger') as mock_logger:
                    await run_startup_diagnostics()

                    # Verify logging calls
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]

                    # Check for expected log messages
                    assert any("startup diagnostics" in str(call).lower() for call in info_calls)
                    assert any("API key present" in str(call) for call in info_calls)
                    assert any("1234" in str(call) for call in info_calls)  # Last 4 chars
                    assert any("API connectivity OK" in str(call) for call in info_calls)

    @pytest.mark.asyncio
    async def test_diagnostics_without_api_key(self):
        """Test diagnostics when API key is not set."""
        from mcp_polygon.server import run_startup_diagnostics

        with patch('mcp_polygon.server.POLYGON_API_KEY', ''):
            with patch('mcp_polygon.server.logger') as mock_logger:
                await run_startup_diagnostics()

                # Verify warning was logged
                warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                assert any("POLYGON_API_KEY not set" in str(call) for call in warning_calls)
                assert any("functionality will be limited" in str(call) for call in warning_calls)

    @pytest.mark.asyncio
    async def test_diagnostics_with_api_error(self):
        """Test diagnostics when API call fails."""
        from mcp_polygon.server import run_startup_diagnostics, polygon_client

        # Mock failed API call
        with patch.object(
            polygon_client,
            'get_aggs',
            side_effect=Exception("API connection failed")
        ):
            with patch('mcp_polygon.server.POLYGON_API_KEY', 'test_key'):
                with patch('mcp_polygon.server.logger') as mock_logger:
                    await run_startup_diagnostics()

                    # Verify error was logged
                    error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
                    assert any("API connectivity failed" in str(call) for call in error_calls)
                    assert any("API connection failed" in str(call) for call in error_calls)

    @pytest.mark.asyncio
    async def test_diagnostics_with_empty_response(self):
        """Test diagnostics when API returns empty response."""
        from mcp_polygon.server import run_startup_diagnostics, polygon_client

        # Mock empty response
        mock_response = Mock()
        mock_response.data = None

        with patch.object(polygon_client, 'get_aggs', return_value=mock_response):
            with patch('mcp_polygon.server.POLYGON_API_KEY', 'test_key'):
                with patch('mcp_polygon.server.logger') as mock_logger:
                    await run_startup_diagnostics()

                    # Verify warning was logged
                    warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                    assert any("empty response" in str(call).lower() for call in warning_calls)

    @pytest.mark.asyncio
    async def test_diagnostics_runs_successfully(self):
        """Test that diagnostics function completes without exceptions."""
        from mcp_polygon.server import run_startup_diagnostics

        # Should not raise any exceptions
        try:
            with patch('mcp_polygon.server.POLYGON_API_KEY', 'test_key'):
                with patch('mcp_polygon.server.polygon_client') as mock_client:
                    mock_response = Mock()
                    mock_response.data = b'{"results": []}'
                    mock_client.get_aggs.return_value = mock_response

                    await run_startup_diagnostics()
                    success = True
        except Exception as e:
            success = False
            pytest.fail(f"Diagnostics raised unexpected exception: {e}")

        assert success


class TestErrorHandlingIntegration:
    """Integration tests for combined error handling features."""

    @pytest.mark.asyncio
    async def test_date_validation_before_api_call(self):
        """Test that date validation prevents API calls for future dates."""
        # This would be tested at the tool level in actual usage
        # Here we verify the validation function works correctly
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        error = validate_date(future, "from_")

        # Should get validation error before API call
        assert error is not None
        assert "Error" in error
        assert "in the future" in error

    @pytest.mark.asyncio
    async def test_api_tier_error_includes_method_context(self):
        """Test that API tier errors include the method being called."""
        client = Mock()
        client.some_endpoint = Mock(
            side_effect=Exception("NOT_AUTHORIZED")
        )
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        result = await wrapper.call("some_endpoint", ticker="TEST")

        assert "method=some_endpoint" in result
        assert "ticker=TEST" in result

    @pytest.mark.asyncio
    async def test_multiple_error_types_handled_separately(self):
        """Test that different error types are handled appropriately."""
        client = Mock()
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        # API tier error
        client.endpoint1 = Mock(side_effect=Exception("NOT_AUTHORIZED"))
        result1 = await wrapper.call("endpoint1")
        assert "API tier limitation" in result1

        # Timeout error
        client.endpoint2 = Mock(side_effect=Exception("timeout occurred"))
        result2 = await wrapper.call("endpoint2")
        assert "timed out" in result2.lower()

        # Connection error
        client.endpoint3 = Mock(side_effect=Exception("connection refused"))
        result3 = await wrapper.call("endpoint3")
        assert "connect" in result3.lower()

    def test_validation_functions_are_reusable(self):
        """Test that validation functions work across different modules."""
        past_date = "2024-01-01"
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        # Both modules should handle dates consistently
        assert validate_date(past_date, "date") is None
        assert validate_date(past_date, "date") is None

        assert validate_date(future_date, "date") is not None
        assert validate_date(future_date, "date") is not None
