"""
WebSocket streaming tools for indices market.

Requires Indices API subscription tier. Subscribe at polygon.io/pricing

Indices have a unique V.I:* channel for real-time index values, and do not
provide trade or quote streams (only values and aggregates).

Documentation References:
- Connection Guide: polygon-docs/websockets/quickstart.md:65-103
- Authentication: polygon-docs/websockets/quickstart.md:146-175
- Indices Overview: polygon-docs/websockets/indices/overview.md:90-117
- Index Values (V.I:*): polygon-docs/websockets/indices/index-value.md
- Minute Agg (AM.I:*): polygon-docs/websockets/indices/aggregates-per-minute.md
- Second Agg (AS.I:*): polygon-docs/websockets/indices/aggregates-per-second.md
"""

import os
from typing import List, Optional
from mcp.types import ToolAnnotations
from .connection_manager import ConnectionManager
from .stream_formatter import format_connection_status


def register_tools(mcp, connection_manager: ConnectionManager):
    """
    Register WebSocket streaming tools for indices market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_indices_stream(
        channels: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> str:
        """
        Start streaming indices market data via WebSocket.

        Requires Indices API subscription tier.

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Market Overview: polygon-docs/websockets/indices/overview.md:90-117
        - Index Values: polygon-docs/websockets/indices/index-value.md
        - Minute Agg: polygon-docs/websockets/indices/aggregates-per-minute.md
        - Second Agg: polygon-docs/websockets/indices/aggregates-per-second.md

        Channels:
        - V.I:* (index values) - Real-time index value updates
        - AM.I:* (minute agg) - One-minute aggregate bars
        - AS.I:* (second agg) - One-second aggregate bars

        Note: Indices do not provide trade or quote streams (only values and aggregates).

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.I:SYMBOL"
                     Examples: ["V.I:SPX", "AM.I:DJI", "AS.I:NDX"]
                     Symbol format: I:SYMBOL (e.g., I:SPX, I:DJI, I:NDX, I:RUT)
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: wss://socket.polygon.io/indices)

        Returns:
            Status message including:
            - Connection endpoint
            - List of subscribed channels
            - Message reception statistics (total received, buffer fill level)
            - Sample of recent messages (up to 5 formatted messages)

            Message samples demonstrate that data is flowing and allow verification
            of subscription success. Use get_indices_stream_status() to check
            buffer state without message samples.

        Note:
            Messages are buffered (last 100) in memory. The buffer is automatically
            managed (FIFO eviction when full) and cleared on disconnect. Buffer
            statistics show total messages received vs currently buffered.

            Indices have a unique V.I:* channel for real-time values. No trade/quote
            streams available (only values and aggregates). Requires Indices API tier.

        Examples:
            Start streaming major indices:
            >>> await start_indices_stream(channels=["V.I:SPX", "V.I:DJI", "V.I:NDX"])

            Subscribe to S&P 500 minute bars:
            >>> await start_indices_stream(channels=["AM.I:SPX"])

            Mixed channels:
            >>> await start_indices_stream(channels=["V.I:SPX", "AM.I:DJI", "AS.I:RUT"])
        """
        try:
            # Default channels if none provided
            if channels is None:
                channels = ["V.I:SPX"]

            # Default endpoint
            if endpoint is None:
                endpoint = "wss://socket.polygon.io/indices"

            # Get or create connection
            conn = connection_manager.get_connection(
                "indices",
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

            return f"""✓ Started indices WebSocket stream
Endpoint: {endpoint}
Channels: {", ".join(channels)}
State: {conn.state.value}

Message Stats:
- Total received: {stats['total_received']}
- Buffered: {stats['buffered']}/{stats['buffer_capacity']}
{sample_text}

Stream is now active. Use get_indices_stream_status() to check buffer state."""

        except Exception as e:
            return f"✗ Failed to start indices stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_indices_stream() -> str:
        """
        Stop indices market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("indices")
            await conn.close()
            return "✓ Stopped indices WebSocket stream"
        except KeyError:
            return "○ No active indices WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop indices stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_indices_stream_status() -> str:
        """
        Get current status of indices WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("indices")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active indices WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_indices_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active indices stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["V.I:SPX", "AM.I:DJI"])

        Returns:
            Confirmation message with updated subscription list

        Examples:
            Subscribe to Russell 2000 index:
            >>> await subscribe_indices_channels(["V.I:RUT"])

            Add minute aggregates:
            >>> await subscribe_indices_channels(["AM.I:SPX", "AM.I:DJI"])
        """
        try:
            conn = connection_manager.get_connection("indices")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to indices stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active indices stream. Use start_indices_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_indices_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active indices stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["V.I:SPX"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("indices")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from indices stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active indices stream. Use start_indices_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_indices_subscriptions() -> str:
        """
        List all active subscriptions for indices stream.

        Groups channels by type: V.I: (values), AM.I: (minute agg), AS.I: (second agg)

        Returns:
            List of subscribed channels grouped by type

        Examples:
            >>> await list_indices_subscriptions()
            # Outputs:
            # Index Values (2): V.I:SPX, V.I:DJI
            # Minute Aggregates (1): AM.I:SPX
        """
        try:
            conn = connection_manager.get_connection("indices")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            # Group channels by type
            channel_groups = {
                "V.I:": [],  # Index values
                "AM.I:": [],  # Minute aggregates
                "AS.I:": [],  # Second aggregates
            }

            for channel in status["subscriptions"]:
                # Match channel prefix patterns
                if channel.startswith("V.I:"):
                    channel_groups["V.I:"].append(channel)
                elif channel.startswith("AM.I:"):
                    channel_groups["AM.I:"].append(channel)
                elif channel.startswith("AS.I:"):
                    channel_groups["AS.I:"].append(channel)

            output = f"Indices Stream Subscriptions ({status['subscription_count']} total):\n\n"

            # Map prefixes to readable names
            channel_names = {
                "V.I:": "Index Values",
                "AM.I:": "Minute Aggregates",
                "AS.I:": "Second Aggregates",
            }

            for prefix, channels in channel_groups.items():
                if not channels:
                    continue

                channel_name = channel_names[prefix]
                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return (
                output.strip()
                if output.strip()
                != f"Indices Stream Subscriptions ({status['subscription_count']} total):"
                else "No subscriptions found"
            )

        except KeyError:
            return "No active indices WebSocket connection"
