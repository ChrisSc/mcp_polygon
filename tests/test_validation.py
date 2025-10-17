"""Tests for shared validation functions."""

import pytest
from datetime import datetime, date, timedelta, timezone
from mcp_polygon.validation import validate_date, validate_date_any_of


class TestDateValidation:
    """Test suite for validate_date() function."""

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


class TestDateAnyOfValidation:
    """Test suite for validate_date_any_of() function."""

    def test_validate_date_any_of_accepts_none(self):
        """Test that None is valid."""
        result = validate_date_any_of(None)
        assert result is None

    def test_validate_date_any_of_accepts_empty_string(self):
        """Test that empty string is valid."""
        result = validate_date_any_of("")
        assert result is None

    def test_validate_date_any_of_accepts_valid_single_date(self):
        """Test single valid past date."""
        result = validate_date_any_of("2024-01-01")
        assert result is None

    def test_validate_date_any_of_accepts_valid_comma_separated_dates(self):
        """Test multiple valid past dates."""
        result = validate_date_any_of("2024-01-01,2024-01-15,2024-02-01")
        assert result is None

    def test_validate_date_any_of_accepts_dates_with_spaces(self):
        """Test dates with spaces around commas are handled."""
        result = validate_date_any_of("2024-01-01, 2024-01-15 , 2024-02-01")
        assert result is None

    def test_validate_date_any_of_rejects_future_date_in_list(self):
        """Test that future date in list is rejected."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        date_list = f"2024-01-01,{future},2024-02-01"

        result = validate_date_any_of(date_list)

        assert result is not None
        assert "Error" in result
        assert "in the future" in result
        assert "date_any_of" in result

    def test_validate_date_any_of_rejects_first_future_date(self):
        """Test that first date being future is caught."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        date_list = f"{future},2024-01-01"

        result = validate_date_any_of(date_list)

        assert result is not None
        assert "Error" in result

    def test_validate_date_any_of_with_single_future_date(self):
        """Test single future date without comma."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()

        result = validate_date_any_of(future)

        assert result is not None
        assert "Error" in result

    def test_validate_date_any_of_invalid_format_ignored(self):
        """Test that invalid formats in list are ignored (let API handle)."""
        # Invalid formats should not cause validation errors
        result = validate_date_any_of("not-a-date,2024-01-01")
        assert result is None

    def test_validate_date_any_of_stops_at_first_error(self):
        """Test that validation stops at first error."""
        future1 = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        future2 = (datetime.now(timezone.utc) + timedelta(days=60)).date().isoformat()
        date_list = f"2024-01-01,{future1},{future2}"

        result = validate_date_any_of(date_list)

        # Should return error for first future date
        assert result is not None
        assert future1 in result


class TestEdgeCases:
    """Additional edge case tests for validation functions."""

    def test_validate_date_leap_year(self):
        """Test validation handles leap year dates correctly."""
        # Feb 29, 2024 is valid (leap year)
        result = validate_date("2024-02-29", "date")
        assert result is None

        # Feb 29, 2023 is invalid (not leap year) - should let API handle
        result = validate_date("2023-02-29", "date")
        assert result is None  # Invalid format is ignored

    def test_validate_date_year_2038_plus(self):
        """Test validation handles timestamps beyond 2038."""
        # Year 2100 timestamp
        future_timestamp = int(datetime(2100, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        result = validate_date(future_timestamp, "timestamp")
        assert result is not None
        assert "in the future" in result

    def test_validate_date_any_of_mixed_valid_invalid(self):
        """Test that mixed list returns error for first invalid date."""
        past1 = "2024-01-01"
        past2 = "2024-02-01"
        future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
        past3 = "2024-03-01"

        # Future date in middle should be caught
        result = validate_date_any_of(f"{past1},{past2},{future},{past3}")
        assert result is not None
        assert "in the future" in result

    def test_validate_date_none_vs_empty_string(self):
        """Test that None and empty string are both accepted."""
        assert validate_date(None, "date") is None
        assert validate_date("", "date") is None
        assert validate_date_any_of(None) is None
        assert validate_date_any_of("") is None

    def test_validate_date_any_of_large_list(self):
        """Test validation with many dates (performance check)."""
        # Create 50 valid past dates
        dates = [
            (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)).date().isoformat()
            for i in range(50)
        ]
        date_list = ",".join(dates)

        # Should validate all without error
        result = validate_date_any_of(date_list)
        assert result is None
