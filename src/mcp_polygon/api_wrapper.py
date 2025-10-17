"""API wrapper for consistent error handling and response formatting."""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class PolygonAPIError:
    """Structured error response formatting for LLM-friendly error messages."""

    @staticmethod
    def format_error(
        operation: str, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format an error message with helpful context for LLM consumption.

        Args:
            operation: Name of the operation that failed (e.g., 'get_aggs')
            error: The exception that occurred
            context: Additional context like ticker, parameters

        Returns:
            Human-readable error message string
        """
        # Build context string if provided
        ctx = ""
        if context:
            ctx = " (" + ", ".join(f"{k}={v}" for k, v in context.items()) + ")"

        # Handle HTTP errors from requests library
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            status = error.response.status_code

            if status == 401:
                return (
                    "Error: Invalid API key. Please check your POLYGON_API_KEY "
                    "environment variable."
                )
            elif status == 403:
                return (
                    f"Error: API key does not have permission to access {operation}. "
                    "Upgrade your plan at polygon.io"
                )
            elif status == 404:
                return (
                    f"Error: Resource not found{ctx}. Please verify the ticker "
                    "symbol or parameters."
                )
            elif status == 429:
                return "Error: Rate limit exceeded. Please wait a moment and try again."
            elif 500 <= status < 600:
                return (
                    f"Error: Polygon API is experiencing issues (status {status}). "
                    "Please try again later."
                )
            else:
                return f"Error: API request failed with status {status}{ctx}"

        # Handle timeout errors
        elif "timeout" in str(type(error)).lower() or "timeout" in str(error).lower():
            return (
                f"Error: Request timed out after 30 seconds{ctx}. "
                "The API may be slow or overloaded."
            )

        # Handle connection errors
        elif (
            "connection" in str(type(error)).lower()
            or "connection" in str(error).lower()
        ):
            return (
                "Error: Could not connect to Polygon API. "
                "Please check your internet connection."
            )

        # Handle all other errors
        else:
            # Log unexpected errors for debugging
            logger.error(
                f"Unexpected error in {operation}: {error}",
                exc_info=True,
                extra=context or {},
            )
            return (
                f"Error: An unexpected error occurred in {operation}. Please try again."
            )


class PolygonAPIWrapper:
    """Wrapper for Polygon API calls with automatic formatting and error handling."""

    def __init__(self, client, formatter: Callable[[str], str]):
        """
        Initialize the API wrapper.

        Args:
            client: Polygon RESTClient instance
            formatter: Function to format JSON responses to CSV (e.g., json_to_csv)
        """
        self.client = client
        self.formatter = formatter

    async def call(self, method_name: str, **kwargs) -> str:
        """
        Call a Polygon API method with automatic error handling and CSV formatting.

        This method:
        1. Resolves the API method by name (handles both regular and vx.* methods)
        2. Calls the method with raw=True to get binary response
        3. Decodes the response and formats it as CSV
        4. Returns helpful error messages on any failures

        Args:
            method_name: API method name (e.g., 'get_aggs', 'list_trades')
                        For vx methods, prefix with 'vx_' (e.g., 'vx_list_stock_financials')
            **kwargs: Parameters to pass to the API method

        Returns:
            CSV-formatted string on success, or error message string on failure

        Examples:
            >>> wrapper = PolygonAPIWrapper(client, json_to_csv)
            >>> await wrapper.call('get_aggs', ticker='AAPL', multiplier=1, ...)
            "timestamp,open,high,low,close,volume\\n1640995200000,150.5,151.2,..."

            >>> await wrapper.call('vx_list_stock_financials', ticker='AAPL', ...)
            "ticker,period,filing_date,revenue\\nAAPL,Q4,2024-01-01,100000000\\n..."
        """
        try:
            # Handle vx.* methods (client.vx.method_name)
            if method_name.startswith("vx_"):
                actual_method_name = method_name[3:]  # Remove 'vx_' prefix
                method = getattr(self.client.vx, actual_method_name)
            else:
                # Regular methods (client.method_name)
                method = getattr(self.client, method_name)

            # Make API call with raw=True to get binary response
            results = method(**kwargs, raw=True)

            # Handle different response types from SDK
            if hasattr(results, "data"):
                # Binary response (most endpoints)
                json_data = results.data.decode("utf-8")
            elif hasattr(results, "__dict__"):
                # Object response (technical indicators, related companies)
                import json

                # Convert object to dict, handling nested objects
                json_data = json.dumps(
                    results,
                    default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
                )
            elif isinstance(results, list):
                # List response
                import json

                json_data = json.dumps(
                    [
                        item.__dict__ if hasattr(item, "__dict__") else item
                        for item in results
                    ]
                )
            else:
                # Fallback to string conversion
                json_data = str(results)

            # Format as CSV
            return self.formatter(json_data)

        except AttributeError as e:
            # Method doesn't exist on client
            return (
                f"Error: API method '{method_name}' not found in Polygon client. "
                f"Details: {e}"
            )

        except Exception as e:
            # Extract context for error messages
            # More context = better debugging for LLM and users
            # Priority: ticker/symbol, dates, then query parameters
            error_msg = str(e)
            context = {"method": method_name}

            # Add ticker/symbol to context
            if "ticker" in kwargs:
                context["ticker"] = kwargs["ticker"]
            elif "from_" in kwargs and "to" in kwargs:
                # Forex/crypto currency pair
                context["currency_pair"] = (
                    f"{kwargs.get('from_', '')}_{kwargs.get('to', '')}"
                )

            # Add date range to context if present
            if "from_" in kwargs and "to" in kwargs and "ticker" in kwargs:
                # Aggregates query with date range
                context["date_range"] = f"{kwargs['from_']} to {kwargs['to']}"
            elif "date" in kwargs:
                # Single date query
                context["date"] = kwargs["date"]

            # Add additional query parameters for better debugging
            if "multiplier" in kwargs and kwargs["multiplier"] is not None:
                context["multiplier"] = kwargs["multiplier"]
            if "timespan" in kwargs and kwargs["timespan"] is not None:
                context["timespan"] = kwargs["timespan"]
            if "limit" in kwargs and kwargs["limit"] is not None:
                context["limit"] = kwargs["limit"]
            if "window" in kwargs and kwargs["window"] is not None:
                context["window"] = kwargs["window"]

            # Check for API tier limitation (NOT_AUTHORIZED)
            if "NOT_AUTHORIZED" in error_msg or "not entitled" in error_msg.lower():
                # Build context string for error message
                ctx_str = ", ".join(f"{k}={v}" for k, v in context.items())
                return (
                    f"API tier limitation: Your Polygon.io plan does not include access to {method_name}. "
                    f"This tool requires a higher subscription tier.\n\n"
                    f"Upgrade at: https://polygon.io/pricing\n\n"
                    f"Context: {ctx_str}\n"
                    f"Details: {error_msg}"
                )

            # Log the full error for debugging
            logger.error(
                f"Error calling {method_name}",
                exc_info=True,
                extra={"kwargs": kwargs, "error": error_msg},
            )

            # Return formatted error message
            return PolygonAPIError.format_error(method_name, e, context)
