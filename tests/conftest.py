"""Pytest fixtures for MCP Polygon tests."""
import pytest
import json
from unittest.mock import Mock
from mcp_polygon.api_wrapper import PolygonAPIWrapper
from mcp_polygon.formatters import json_to_csv


@pytest.fixture
def mock_polygon_client():
    """
    Mock Polygon REST client with vx attribute for vx methods.

    Returns:
        Mock object with client methods that can be configured per test
    """
    client = Mock()
    client.vx = Mock()  # For vx.* methods like vx.list_stock_financials
    return client


@pytest.fixture
def mock_response():
    """
    Factory fixture for creating mock API responses.

    Returns:
        Function that creates a Mock response object with encoded JSON data

    Example:
        def test_something(mock_response):
            data = {"results": [{"ticker": "AAPL", "price": 150}]}
            response = mock_response(data)
            client.get_aggs.return_value = response
    """

    def _make_response(data: dict) -> Mock:
        """Create a mock response with JSON data."""
        response = Mock()
        response.data = json.dumps(data).encode("utf-8")
        return response

    return _make_response


@pytest.fixture
def api_wrapper(mock_polygon_client):
    """
    API wrapper instance with mocked client and real formatter.

    Returns:
        PolygonAPIWrapper instance ready for testing

    Example:
        async def test_get_aggs(api_wrapper, mock_response):
            api_wrapper.client.get_aggs.return_value = mock_response({"results": []})
            result = await api_wrapper.call('get_aggs', ticker='AAPL')
    """
    return PolygonAPIWrapper(mock_polygon_client, json_to_csv)


@pytest.fixture
def sample_aggregate_data():
    """
    Sample aggregate bar data for testing.

    Returns:
        Dict with typical Polygon aggregate response structure
    """
    return {
        "ticker": "AAPL",
        "status": "OK",
        "results": [
            {
                "v": 1000000,  # volume
                "vw": 150.25,  # volume weighted average price
                "o": 149.50,  # open
                "c": 150.75,  # close
                "h": 151.00,  # high
                "l": 149.00,  # low
                "t": 1640995200000,  # timestamp
                "n": 5000,  # number of transactions
            },
            {
                "v": 1200000,
                "vw": 151.50,
                "o": 150.75,
                "c": 151.25,
                "h": 152.00,
                "l": 150.50,
                "t": 1641081600000,
                "n": 6000,
            },
        ],
    }


@pytest.fixture
def sample_trade_data():
    """
    Sample trade data for testing.

    Returns:
        Dict with typical Polygon trade response structure
    """
    return {
        "status": "OK",
        "results": [
            {
                "T": "AAPL",  # ticker
                "t": 1640995200000,  # timestamp
                "y": 1640995200000000000,  # participant timestamp
                "f": 1640995200000000000,  # trf timestamp
                "q": 123456,  # sequence number
                "i": "1234",  # trade id
                "x": 4,  # exchange
                "s": 100,  # size
                "p": 150.25,  # price
                "c": [0, 12],  # conditions
            }
        ],
    }


@pytest.fixture
def sample_ticker_details():
    """
    Sample ticker details data for testing.

    Returns:
        Dict with typical Polygon ticker details response structure
    """
    return {
        "status": "OK",
        "results": {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "stocks",
            "locale": "us",
            "primary_exchange": "XNAS",
            "type": "CS",
            "active": True,
            "currency_name": "usd",
            "cik": "0000320193",
            "composite_figi": "BBG000B9XRY4",
            "share_class_figi": "BBG001S5N8V8",
        },
    }
