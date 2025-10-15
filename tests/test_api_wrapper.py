"""Tests for the API wrapper module."""

import pytest
from unittest.mock import Mock
from mcp_polygon.api_wrapper import PolygonAPIError


def make_http_error(status_code: int) -> Exception:
    """Create a mock HTTP error with proper response structure."""
    error = Exception(f"HTTP {status_code} error")
    error.response = Mock(status_code=status_code)
    return error


class TestPolygonAPIError:
    """Tests for PolygonAPIError error formatting."""

    def test_format_401_error(self):
        """Test formatting of 401 Unauthorized error."""
        error = Mock()
        error.response = Mock(status_code=401)

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "Invalid API key" in result
        assert "POLYGON_API_KEY" in result

    def test_format_403_error(self):
        """Test formatting of 403 Forbidden error."""
        error = Mock()
        error.response = Mock(status_code=403)

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "permission" in result
        assert "polygon.io" in result

    def test_format_404_error(self):
        """Test formatting of 404 Not Found error."""
        error = Mock()
        error.response = Mock(status_code=404)

        result = PolygonAPIError.format_error("get_aggs", error, {"ticker": "INVALID"})

        assert "Error" in result
        assert "not found" in result
        assert "INVALID" in result

    def test_format_429_error(self):
        """Test formatting of 429 Rate Limit error."""
        error = Mock()
        error.response = Mock(status_code=429)

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "Rate limit" in result
        assert "try again" in result

    def test_format_500_error(self):
        """Test formatting of 500 Server Error."""
        error = Mock()
        error.response = Mock(status_code=500)

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "Polygon API" in result
        assert "500" in result

    def test_format_timeout_error(self):
        """Test formatting of timeout error."""
        error = Exception("timeout occurred")

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "timed out" in result.lower() or "timeout" in result.lower()

    def test_format_connection_error(self):
        """Test formatting of connection error."""
        error = Exception("connection refused")

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "connect" in result.lower()
        assert "internet" in result.lower()

    def test_format_generic_error(self):
        """Test formatting of generic unexpected error."""
        error = Exception("Something unexpected")

        result = PolygonAPIError.format_error("get_aggs", error)

        assert "Error" in result
        assert "unexpected" in result.lower()
        assert "get_aggs" in result

    def test_error_with_context(self):
        """Test that context is included in error message."""
        error = Mock()
        error.response = Mock(status_code=404)
        context = {"ticker": "AAPL", "date": "2024-01-01"}

        result = PolygonAPIError.format_error("get_aggs", error, context)

        assert "AAPL" in result
        assert "2024-01-01" in result


class TestPolygonAPIWrapper:
    """Tests for PolygonAPIWrapper functionality."""

    @pytest.mark.asyncio
    async def test_successful_api_call(
        self, api_wrapper, mock_response, sample_aggregate_data
    ):
        """Test successful API call returns formatted CSV."""
        # Setup mock
        api_wrapper.client.get_aggs.return_value = mock_response(sample_aggregate_data)

        # Make call
        result = await api_wrapper.call(
            "get_aggs",
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_="2024-01-01",
            to="2024-01-31",
        )

        # Verify
        assert isinstance(result, str)
        assert len(result) > 0
        # CSV should contain headers and data
        assert "v" in result or "volume" in result or "1000000" in result
        api_wrapper.client.get_aggs.assert_called_once()

    @pytest.mark.asyncio
    async def test_vx_method_call(self, api_wrapper, mock_response):
        """Test that vx_* methods are routed to client.vx.*"""
        data = {"results": [{"ticker": "AAPL", "revenue": 1000000}]}
        api_wrapper.client.vx.list_stock_financials.return_value = mock_response(data)

        result = await api_wrapper.call("vx_list_stock_financials", ticker="AAPL")

        assert isinstance(result, str)
        assert len(result) > 0
        api_wrapper.client.vx.list_stock_financials.assert_called_once()

    @pytest.mark.asyncio
    async def test_method_not_found(self, api_wrapper):
        """Test handling of non-existent API method."""
        # Replace client with a spec'd mock that doesn't have invalid_method
        limited_client = Mock(spec=["get_aggs", "vx"])
        limited_client.vx = Mock()
        api_wrapper.client = limited_client

        result = await api_wrapper.call("invalid_method", ticker="AAPL")

        assert "Error" in result
        assert "not found" in result
        assert "invalid_method" in result

    @pytest.mark.asyncio
    async def test_http_401_error(self, api_wrapper):
        """Test handling of 401 authentication error."""
        api_wrapper.client.get_aggs.side_effect = make_http_error(401)

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "Invalid API key" in result

    @pytest.mark.asyncio
    async def test_http_404_error(self, api_wrapper):
        """Test handling of 404 not found error."""
        api_wrapper.client.get_aggs.side_effect = make_http_error(404)

        result = await api_wrapper.call("get_aggs", ticker="INVALID")

        assert "Error" in result
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_http_429_error(self, api_wrapper):
        """Test handling of 429 rate limit error."""
        api_wrapper.client.get_aggs.side_effect = make_http_error(429)

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "Rate limit" in result

    @pytest.mark.asyncio
    async def test_http_500_error(self, api_wrapper):
        """Test handling of 500 server error."""
        api_wrapper.client.get_aggs.side_effect = make_http_error(500)

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "500" in result

    @pytest.mark.asyncio
    async def test_timeout_error(self, api_wrapper):
        """Test handling of timeout error."""
        api_wrapper.client.get_aggs.side_effect = Exception("Request timeout")

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "timed out" in result.lower() or "timeout" in result.lower()

    @pytest.mark.asyncio
    async def test_connection_error(self, api_wrapper):
        """Test handling of connection error."""
        api_wrapper.client.get_aggs.side_effect = Exception("Connection refused")

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "connect" in result.lower()

    @pytest.mark.asyncio
    async def test_generic_exception(self, api_wrapper):
        """Test handling of generic unexpected exception."""
        api_wrapper.client.get_aggs.side_effect = Exception("Unexpected error")

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        assert "Error" in result
        assert "unexpected" in result.lower()

    @pytest.mark.asyncio
    async def test_context_in_error_messages(self, api_wrapper):
        """Test that error messages include context like ticker."""
        api_wrapper.client.get_aggs.side_effect = make_http_error(404)

        result = await api_wrapper.call("get_aggs", ticker="TEST123")

        # Context should be in the error message
        assert "Error" in result
        assert "TEST123" in result

    @pytest.mark.asyncio
    async def test_multiple_parameters(
        self, api_wrapper, mock_response, sample_aggregate_data
    ):
        """Test that all parameters are passed through correctly."""
        api_wrapper.client.get_aggs.return_value = mock_response(sample_aggregate_data)

        await api_wrapper.call(
            "get_aggs",
            ticker="AAPL",
            multiplier=5,
            timespan="minute",
            from_="2024-01-01",
            to="2024-01-02",
            adjusted=True,
            sort="desc",
            limit=100,
        )

        # Verify call was made with correct parameters
        call_args = api_wrapper.client.get_aggs.call_args
        assert call_args is not None
        kwargs = call_args.kwargs
        assert kwargs["ticker"] == "AAPL"
        assert kwargs["multiplier"] == 5
        assert kwargs["timespan"] == "minute"
        assert kwargs["raw"] is True

    @pytest.mark.asyncio
    async def test_binary_response_decoding(self, api_wrapper, mock_polygon_client):
        """Test that binary responses are correctly decoded."""
        # Create mock response with binary data
        import json

        mock_response = Mock()
        test_data = {"results": [{"test": "data"}]}
        mock_response.data = json.dumps(test_data).encode("utf-8")
        mock_polygon_client.get_aggs.return_value = mock_response

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        # Should successfully decode and format
        assert isinstance(result, str)
        assert "test" in result or "data" in result

    @pytest.mark.asyncio
    async def test_empty_results(self, api_wrapper, mock_response):
        """Test handling of empty results from API."""
        empty_data = {"results": []}
        api_wrapper.client.get_aggs.return_value = mock_response(empty_data)

        result = await api_wrapper.call("get_aggs", ticker="AAPL")

        # Should return empty string (CSV with no data)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_forex_pair_context(self, api_wrapper):
        """Test that forex pairs are included in error context."""
        api_wrapper.client.get_last_forex_quote.side_effect = make_http_error(404)

        result = await api_wrapper.call("get_last_forex_quote", from_="USD", to="EUR")

        assert "Error" in result
        # Should include currency pair in context
        assert "USD" in result or "EUR" in result
