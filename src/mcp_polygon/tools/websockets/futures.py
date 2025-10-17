"""
WebSocket streaming tools for futures market (Beta).

Futures WebSocket API is in Beta. Symbol format: ROOTMYY (e.g., ESZ24, GCZ24)
where ROOT is the futures symbol, M is the month code, YY is the year.

Documentation References:
- Futures Overview: polygon-docs/websockets/futures/overview.md:1-343
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
    Register WebSocket streaming tools for futures market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_futures_stream(
        channels: List[str],
        api_key: Optional[str] = None,
        endpoint: str = "wss://socket.polygon.io/futures",
    ) -> str:
        """
        Start real-time futures market data stream (Beta).

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Futures Overview: polygon-docs/websockets/futures/overview.md:90-117
        - Trades Channel (T.*): polygon-docs/websockets/futures/trades.md:1-50
        - Quotes Channel (Q.*): polygon-docs/websockets/futures/quotes.md:1-50
        - Minute Agg (AM.*): polygon-docs/websockets/futures/aggregates-per-minute.md:1-50
        - Second Agg (AS.*): polygon-docs/websockets/futures/aggregates-per-second.md:1-50

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.SYMBOL"
                     Examples: ["T.ESZ24", "Q.GCZ24", "AM.*"]
                     Prefixes: T (trades), Q (quotes), AM (minute agg), AS (second agg)
                     Symbol Format: ROOTMYY
                                   (e.g., ESZ24 = ES December 2024)
                                   Month codes: F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun,
                                               N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: real-time)

        Returns:
            Status message including:
            - Connection endpoint
            - List of subscribed channels
            - Message reception statistics (total received, buffer fill level)
            - Sample of recent messages (up to 5 formatted messages)

            Message samples demonstrate that data is flowing and allow verification
            of subscription success. Use get_futures_stream_status() to check
            buffer state without message samples.

        Note:
            Messages are buffered (last 100) in memory. The buffer is automatically
            managed (FIFO eviction when full) and cleared on disconnect. Buffer
            statistics show total messages received vs currently buffered.

            Futures WebSocket API is in Beta. Symbol format: ROOTMYY (e.g., ESZ24).

        Examples:
            - start_futures_stream(["T.ESZ24", "Q.ESZ24"])
              → Stream E-mini S&P 500 Dec 2024 trades and quotes
            - start_futures_stream(["AM.*"])
              → Stream all futures minute aggregates (high volume!)
            - start_futures_stream(["T.GCZ24", "T.CLZ24"])
              → Stream gold and crude oil futures trades
        """
        try:
            # Get or create connection
            conn = connection_manager.get_connection(
                "futures",
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

            return f"""✓ Started futures WebSocket stream (Beta)
Endpoint: {endpoint}
Channels: {", ".join(channels)}
State: {conn.state.value}

Message Stats:
- Total received: {stats['total_received']}
- Buffered: {stats['buffered']}/{stats['buffer_capacity']}
{sample_text}

Stream is now active. Use get_futures_stream_status() to check buffer state."""

        except Exception as e:
            return f"✗ Failed to start futures stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_futures_stream() -> str:
        """
        Stop futures market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("futures")
            await conn.close()
            return "✓ Stopped futures WebSocket stream"
        except KeyError:
            return "○ No active futures WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop futures stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_futures_stream_status() -> str:
        """
        Get current status of futures WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("futures")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active futures WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_futures_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active futures stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["T.NQZ24", "Q.YMZ24"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("futures")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to futures stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active futures stream. Use start_futures_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_futures_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active futures stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["T.ESZ24"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("futures")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from futures stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active futures stream. Use start_futures_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_futures_subscriptions() -> str:
        """
        List all active subscriptions for futures stream.

        Returns:
            List of subscribed channels grouped by type
        """
        try:
            conn = connection_manager.get_connection("futures")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status["subscriptions"]:
                prefix = channel.split(".")[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Futures Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    "T": "Trades (T.*)",
                    "Q": "Quotes (Q.*)",
                    "AM": "Minute Aggregates (AM.*)",
                    "AS": "Second Aggregates (AS.*)",
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active futures WebSocket connection"
