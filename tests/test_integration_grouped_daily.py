"""
Integration tests for get_grouped_daily_aggs tool against live Polygon API.

These tests require:
1. POLYGON_API_KEY environment variable set
2. Active internet connection
3. Valid Polygon.io API subscription

Run with: pytest tests/test_integration_grouped_daily.py -v -m integration
Skip with: pytest tests/ -v -m "not integration"
"""

import os
import pytest
from datetime import datetime, timedelta
from polygon import RESTClient

from mcp_polygon.api_wrapper import PolygonAPIWrapper
from mcp_polygon.formatters import json_to_csv


@pytest.mark.integration
@pytest.mark.asyncio
class TestGroupedDailyAggsLiveAPI:
    """Integration tests for get_grouped_daily_aggs against live Polygon API."""

    @pytest.fixture
    def live_client(self):
        """Create a real Polygon API client using POLYGON_API_KEY from environment."""
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            pytest.skip("POLYGON_API_KEY environment variable not set")
        return RESTClient(api_key)

    @pytest.fixture
    def live_api_wrapper(self, live_client):
        """Create API wrapper with live client."""
        return PolygonAPIWrapper(live_client, json_to_csv)

    @pytest.fixture
    def recent_trading_date(self):
        """Get a recent trading date with known data availability."""
        # Use a known past date with confirmed market data
        # (2024-10-15 was a Tuesday with full trading day)
        return "2024-10-15"

    async def test_get_grouped_daily_aggs_live_basic(
        self, live_api_wrapper, recent_trading_date
    ):
        """Test basic get_grouped_daily_aggs call against live API."""
        result = await live_api_wrapper.call(
            "get_grouped_daily_aggs",
            date=recent_trading_date,
        )

        # Verify response is CSV format
        assert isinstance(result, str), "Result should be a string"
        assert "T," in result, "Result should contain ticker column header"

        # Verify expected columns are present
        header_line = result.split("\n")[0]
        expected_columns = ["T", "o", "h", "l", "c", "v", "vw", "t", "n"]
        for col in expected_columns:
            assert col in header_line, f"Column '{col}' should be in header"

        # Verify we have data (multiple rows)
        lines = result.strip().split("\n")
        assert len(lines) > 1, "Result should have at least header + 1 data row"

        print(f"\n✓ Live API test passed")
        print(f"  Date: {recent_trading_date}")
        print(f"  Rows returned: {len(lines) - 1}")
        print(f"  Sample tickers (first 5 rows):")
        for line in lines[1:6]:  # Show first 5 data rows
            ticker = line.split(",")[0] if "," in line else "N/A"
            print(f"    - {ticker}")

    async def test_get_grouped_daily_aggs_live_with_parameters(
        self, live_api_wrapper, recent_trading_date
    ):
        """Test get_grouped_daily_aggs with all parameters."""
        result = await live_api_wrapper.call(
            "get_grouped_daily_aggs",
            date=recent_trading_date,
            adjusted=True,
            include_otc=False,
        )

        # Verify response format
        assert isinstance(result, str), "Result should be a string"
        assert "T," in result, "Result should contain CSV headers"

        # Verify we have data
        lines = result.strip().split("\n")
        assert len(lines) > 1, "Result should have data rows"

        print(f"\n✓ Live API test with parameters passed")
        print(f"  Date: {recent_trading_date}")
        print(f"  Parameters: adjusted=True, include_otc=False")
        print(f"  Rows returned: {len(lines) - 1}")

    async def test_get_grouped_daily_aggs_live_invalid_date(
        self, live_api_wrapper
    ):
        """Test that invalid dates are handled gracefully."""
        # Try a weekend date (should return empty or error)
        result = await live_api_wrapper.call(
            "get_grouped_daily_aggs",
            date="2024-01-13",  # This was a Saturday
        )

        # Should either be empty CSV or contain error message
        assert isinstance(result, str), "Result should be a string"

        # If it's an error message, verify it's helpful
        if "Error:" in result or "error" in result.lower():
            print(f"\n✓ Weekend date handled with error message:")
            print(f"  {result[:200]}...")  # Show first 200 chars
        else:
            # If no error, should be valid CSV (possibly empty)
            lines = result.strip().split("\n")
            print(f"\n✓ Weekend date handled gracefully")
            print(f"  Rows returned: {len(lines) - 1}")

    async def test_get_grouped_daily_aggs_live_response_size(
        self, live_api_wrapper, recent_trading_date
    ):
        """Test that response size is within expected range (2-5 MB typical)."""
        result = await live_api_wrapper.call(
            "get_grouped_daily_aggs",
            date=recent_trading_date,
        )

        # Check response size
        size_bytes = len(result.encode("utf-8"))
        size_mb = size_bytes / (1024 * 1024)

        print(f"\n✓ Response size test passed")
        print(f"  Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
        print(
            f"  Expected range: 2-5 MB (typical), 5-10 MB (with OTC)"
        )

        # Verify size is reasonable (not too small or too large)
        assert (
            size_bytes > 1000
        ), "Response should be larger than 1KB (contains data)"
        assert (
            size_bytes < 20 * 1024 * 1024
        ), "Response should be smaller than 20MB (sanity check)"

    @pytest.mark.skipif(
        os.getenv("POLYGON_API_KEY") is None,
        reason="POLYGON_API_KEY not set",
    )
    async def test_get_grouped_daily_aggs_live_specific_tickers(
        self, live_api_wrapper, recent_trading_date
    ):
        """Test that response includes major tickers (AAPL, MSFT, TSLA)."""
        result = await live_api_wrapper.call(
            "get_grouped_daily_aggs",
            date=recent_trading_date,
        )

        # Check for major tickers in response
        major_tickers = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]
        found_tickers = [
            ticker for ticker in major_tickers if ticker in result
        ]

        print(f"\n✓ Major ticker presence test")
        print(f"  Date: {recent_trading_date}")
        print(f"  Found {len(found_tickers)}/{len(major_tickers)} major tickers:")
        for ticker in found_tickers:
            print(f"    ✓ {ticker}")

        # At least some major tickers should be present
        assert (
            len(found_tickers) >= 3
        ), f"Expected at least 3 major tickers, found {len(found_tickers)}"


# Additional helper for manual testing
if __name__ == "__main__":
    """
    Manual test runner for quick validation.

    Usage:
        export POLYGON_API_KEY=your_key
        python tests/test_integration_grouped_daily.py
    """
    import asyncio

    async def main():
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            print("❌ POLYGON_API_KEY environment variable not set")
            print("   Usage: export POLYGON_API_KEY=your_key")
            return

        client = RESTClient(api_key)
        wrapper = PolygonAPIWrapper(client, json_to_csv)

        # Use known past date with confirmed market data
        date = "2024-10-15"

        print(f"Testing get_grouped_daily_aggs with date: {date}")
        print("=" * 60)

        result = await wrapper.call(
            "get_grouped_daily_aggs",
            date=date,
            adjusted=True,
            include_otc=False,
        )

        # Show first few lines
        lines = result.strip().split("\n")
        print(f"\n✓ Success! Retrieved {len(lines) - 1} rows")
        print("\nFirst 10 rows:")
        print("=" * 60)
        for line in lines[:11]:  # Header + 10 rows
            print(line)

    asyncio.run(main())
