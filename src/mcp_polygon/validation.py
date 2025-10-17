"""Shared validation functions for REST API tools."""

from typing import Optional, Union
from datetime import datetime, date, timedelta, timezone


def validate_date(
    date_param: Union[str, int, datetime, date, None], param_name: str
) -> Optional[str]:
    """
    Validate date is not in future. Returns error message if invalid.

    Polygon.io REST API only provides historical data, not future data.
    This validation prevents user confusion and unnecessary API calls.

    Args:
        date_param: Date parameter to validate (string, int timestamp, datetime, or date)
        param_name: Name of the parameter for error message (e.g., "from_", "to", "date")

    Returns:
        Error message string if validation fails, None if valid

    Examples:
        >>> validate_date("2024-01-01", "date")  # Past date - valid
        None

        >>> validate_date("2099-01-01", "date")  # Future date - invalid
        "Error: Date parameter 'date' is in the future..."

        >>> validate_date(None, "date")  # None allowed
        None
    """
    if not date_param:
        return None

    try:
        now = datetime.now(timezone.utc)

        # Handle different date formats
        if isinstance(date_param, datetime):
            date_obj = date_param
            if date_obj.tzinfo is None:
                # Assume UTC if no timezone
                date_obj = date_obj.replace(tzinfo=timezone.utc)
        elif isinstance(date_param, date):
            # Convert date to datetime at midnight UTC
            date_obj = datetime.combine(date_param, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
        elif isinstance(date_param, int):
            # Unix timestamp (milliseconds)
            date_obj = datetime.fromtimestamp(date_param / 1000, tz=timezone.utc)
        else:
            # String - try ISO format
            date_str = str(date_param).replace("Z", "+00:00")
            date_obj = datetime.fromisoformat(date_str)
            if date_obj.tzinfo is None:
                date_obj = date_obj.replace(tzinfo=timezone.utc)

        # Allow slight future dates (1 day tolerance for timezone edge cases)
        if date_obj > now + timedelta(days=1):
            return (
                f"Error: Date parameter '{param_name}' is in the future ({date_param}). "
                f"Current date: {now.date()}. Polygon.io provides historical data only. "
                f"For real-time data, use WebSocket streaming tools."
            )
    except (ValueError, AttributeError, TypeError):
        # Let API handle format errors
        pass

    return None


def validate_date_any_of(date_any_of: Optional[str]) -> Optional[str]:
    """
    Validate comma-separated date list. Returns error if any date is invalid.

    Used for endpoints that accept multiple dates via comma-separated string
    (e.g., "2024-01-01,2024-02-01,2024-03-01").

    Args:
        date_any_of: Comma-separated date string

    Returns:
        Error message string if validation fails, None if valid

    Examples:
        >>> validate_date_any_of("2024-01-01,2024-02-01")
        None

        >>> validate_date_any_of("2024-01-01,2099-01-01")  # Future date
        "Error: Date parameter 'date_any_of' is in the future..."

        >>> validate_date_any_of(None)
        None
    """
    if not date_any_of:
        return None

    # Split and validate each date
    for date_str in date_any_of.split(","):
        date_str = date_str.strip()
        if error := validate_date(date_str, "date_any_of"):
            return error

    return None
