"""
WebSocket streaming tools for forex market.

Forex market operates 24/5 (closed weekends). Symbol format: FROM/TO (e.g., EUR/USD, GBP/JPY)

Documentation References:
- Forex Overview: polygon-docs/websockets/forex/overview.md:1-343
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
    Register WebSocket streaming tools for forex market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_forex_stream(
        channels: List[str],
        api_key: Optional[str] = None,
        endpoint: str = "wss://socket.polygon.io/forex",
    ) -> str:
        """
        Start real-time forex market data stream.

        Forex market operates 24/5 (Sunday 5pm ET to Friday 5pm ET).

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Forex Overview: polygon-docs/websockets/forex/overview.md:90-117
        - Quotes Channel (C.*): polygon-docs/websockets/forex/quotes.md:1-50
        - Minute Agg (CA.*): polygon-docs/websockets/forex/aggregates-per-minute.md:1-50
        - Second Agg (CAS.*): polygon-docs/websockets/forex/aggregates-per-second.md:1-50
        - FMV (FMV.*): polygon-docs/websockets/forex/fair-market-value.md:1-50

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.FROM/TO"
                     Examples: ["C.EUR/USD", "CA.GBP/JPY", "CA.*"]
                     Prefixes: C (quotes), CA (minute agg), CAS (second agg), FMV (fair value)
                     Symbol Format: FROM/TO
                                   (e.g., EUR/USD, GBP/JPY, USD/JPY)
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: real-time)

        Returns:
            Status message indicating stream started

        Examples:
            - start_forex_stream(["C.EUR/USD", "C.GBP/USD"])
              → Stream EUR/USD and GBP/USD quotes
            - start_forex_stream(["CA.*"])
              → Stream all forex minute aggregates (high volume!)
            - start_forex_stream(["FMV.EUR/USD", "FMV.GBP/JPY"])
              → Stream fair market value for currency pairs
        """
        try:
            # Get or create connection
            conn = connection_manager.get_connection(
                "forex",
                endpoint=endpoint,
                api_key=api_key or os.getenv("POLYGON_API_KEY"),
            )

            # Connect and authenticate
            await conn.connect()

            # Subscribe to channels
            await conn.subscribe(channels)

            return f"""✓ Started forex WebSocket stream
Endpoint: {endpoint}
Channels: {", ".join(channels)}
State: {conn.state.value}

Stream is now active. Messages will be delivered as market data arrives.
Market hours: 24/5 (Sunday 5pm ET to Friday 5pm ET)
Use stop_forex_stream() to terminate the connection."""

        except Exception as e:
            return f"✗ Failed to start forex stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_forex_stream() -> str:
        """
        Stop forex market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("forex")
            await conn.close()
            return "✓ Stopped forex WebSocket stream"
        except KeyError:
            return "○ No active forex WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop forex stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_forex_stream_status() -> str:
        """
        Get current status of forex WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("forex")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active forex WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_forex_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active forex stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["C.USD/JPY", "CA.EUR/GBP"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("forex")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to forex stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active forex stream. Use start_forex_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_forex_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active forex stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["C.EUR/USD"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("forex")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from forex stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active forex stream. Use start_forex_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_forex_subscriptions() -> str:
        """
        List all active subscriptions for forex stream.

        Returns:
            List of subscribed channels grouped by type
        """
        try:
            conn = connection_manager.get_connection("forex")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status["subscriptions"]:
                prefix = channel.split(".")[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Forex Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    "C": "Quotes (C.*)",
                    "CA": "Minute Aggregates (CA.*)",
                    "CAS": "Second Aggregates (CAS.*)",
                    "FMV": "Fair Market Value (FMV.*)",
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active forex WebSocket connection"
