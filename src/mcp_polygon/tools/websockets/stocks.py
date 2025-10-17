"""
WebSocket streaming tools for stocks market.

Documentation References:
- Stocks Overview: polygon-docs/websockets/stocks/overview.md:1-343
- Connection Guide: polygon-docs/websockets/quickstart.md:1-1176
- Channel Reference: polygon-docs/websockets/INDEX_AGENT.md:29-48
"""

import os
from typing import List, Optional
from mcp.types import ToolAnnotations
from .connection_manager import ConnectionManager
from .stream_formatter import format_connection_status


def register_tools(mcp, connection_manager: ConnectionManager):
    """
    Register WebSocket streaming tools for stocks market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_stocks_stream(
        channels: List[str],
        api_key: Optional[str] = None,
        endpoint: str = "wss://socket.polygon.io/stocks",
    ) -> str:
        """
        Start real-time stock market data stream.

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Stocks Overview: polygon-docs/websockets/stocks/overview.md:90-117
        - Trades Channel (T.*): polygon-docs/websockets/stocks/trades.md:1-50
        - Quotes Channel (Q.*): polygon-docs/websockets/stocks/quotes.md:1-50
        - Minute Agg (AM.*): polygon-docs/websockets/stocks/aggregates-per-minute.md:1-50
        - Second Agg (A.*): polygon-docs/websockets/stocks/aggregates-per-second.md:1-50
        - LULD (LULD.*): polygon-docs/websockets/stocks/luld.md:1-50
        - FMV (FMV.*): polygon-docs/websockets/stocks/fair-market-value.md:1-50

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.SYMBOL"
                     Examples: ["T.AAPL", "Q.MSFT", "AM.*"]
                     Prefixes: T (trades), Q (quotes), AM (minute agg), A (second agg),
                              LULD (halts), FMV (fair value)
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: real-time)
                     Use "wss://delayed.polygon.io/stocks" for 15-min delayed data

        Returns:
            Status message including:
            - Connection endpoint (real-time or delayed based on API plan)
            - List of subscribed channels
            - Message reception statistics (total received, buffer fill level)
            - Sample of recent messages (up to 5 formatted messages)

            Message samples demonstrate that data is flowing and allow verification
            of subscription success. Use get_stocks_stream_status() to check
            buffer state without message samples.

        Note:
            Messages are buffered (last 100) in memory. The buffer is automatically
            managed (FIFO eviction when full) and cleared on disconnect. Buffer
            statistics show total messages received vs currently buffered.

            For 15-minute delayed data plans, the endpoint automatically switches
            to wss://delayed.polygon.io/stocks based on your API key.

        Examples:
            Start streaming Apple trades and quotes:
            >>> start_stocks_stream(["T.AAPL", "Q.AAPL"])
            ✓ Started stocks WebSocket stream
            ...
            Sample Messages (5):
            [Trade] AAPL @ $150.25, 100 shares
            ...

            Stream all minute aggregates (high volume):
            >>> start_stocks_stream(["AM.*"])

            Stream trades for multiple symbols:
            >>> start_stocks_stream(["T.AAPL", "T.MSFT", "T.TSLA"])
        """
        try:
            # Get or create connection
            conn = connection_manager.get_connection(
                "stocks",
                endpoint=endpoint,
                api_key=api_key or os.getenv("POLYGON_API_KEY"),
            )

            # Connect and authenticate
            await conn.connect()

            # Subscribe to channels
            await conn.subscribe(channels)

            # Get message stats and samples
            stats = conn.get_message_stats()
            recent = conn.get_recent_messages(limit=5)

            # Format sample messages
            from .stream_formatter import format_stream_message
            formatted_samples = []
            for msg in recent:
                try:
                    formatted = format_stream_message(msg, pretty=False)
                    formatted_samples.append(formatted)
                except Exception:
                    pass  # Skip malformed messages

            sample_text = ""
            if formatted_samples:
                sample_text = f"\n\nSample Messages ({len(formatted_samples)}):\n" + "\n\n".join(formatted_samples[:5])

            return f"""✓ Started stocks WebSocket stream
Endpoint: {endpoint}
Channels: {", ".join(channels)}
State: {conn.state.value}

Message Stats:
- Total received: {stats['total_received']}
- Buffered: {stats['buffered']}/{stats['buffer_capacity']}
{sample_text}

Stream is now active. Use get_stocks_stream_status() to check buffer state."""

        except Exception as e:
            return f"✗ Failed to start stocks stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_stocks_stream() -> str:
        """
        Stop stock market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("stocks")
            await conn.close()
            return "✓ Stopped stocks WebSocket stream"
        except KeyError:
            return "○ No active stocks WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop stocks stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_stocks_stream_status() -> str:
        """
        Get current status of stocks WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("stocks")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active stocks WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_stocks_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active stocks stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["T.NVDA", "Q.AMD"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("stocks")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to stocks stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active stocks stream. Use start_stocks_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_stocks_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active stocks stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["T.AAPL"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("stocks")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from stocks stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active stocks stream. Use start_stocks_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_stocks_subscriptions() -> str:
        """
        List all active subscriptions for stocks stream.

        Returns:
            List of subscribed channels
        """
        try:
            conn = connection_manager.get_connection("stocks")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status["subscriptions"]:
                prefix = channel.split(".")[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Stocks Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    "T": "Trades",
                    "Q": "Quotes",
                    "AM": "Minute Aggregates",
                    "A": "Second Aggregates",
                    "LULD": "Limit Up/Limit Down",
                    "FMV": "Fair Market Value",
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active stocks WebSocket connection"
