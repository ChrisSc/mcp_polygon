"""
WebSocket streaming tools for options market.

Documentation References:
- Options Overview: polygon-docs/websockets/options/overview.md:1-343
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
    Register WebSocket streaming tools for options market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_options_stream(
        channels: List[str],
        api_key: Optional[str] = None,
        endpoint: str = "wss://socket.polygon.io/options",
    ) -> str:
        """
        Start real-time options market data stream.

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Options Overview: polygon-docs/websockets/options/overview.md:90-117
        - Trades Channel (T.O:*): polygon-docs/websockets/options/trades.md:1-50
        - Quotes Channel (Q.O:*): polygon-docs/websockets/options/quotes.md:1-50
        - Minute Agg (AM.O:*): polygon-docs/websockets/options/aggregates-per-minute.md:1-50
        - Second Agg (AS.O:*): polygon-docs/websockets/options/aggregates-per-second.md:1-50
        - FMV (FMV.O:*): polygon-docs/websockets/options/fair-market-value.md:1-50

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.O:SYMBOL"
                     Examples: ["T.O:SPY251219C00650000", "Q.O:AAPL250117P00150000", "AM.O:*"]
                     Prefixes: T.O: (trades), Q.O: (quotes), AM.O: (minute agg),
                              AS.O: (second agg), FMV.O: (fair value)
                     Symbol Format: O:ROOT YYMMDDCP PPPPPPPP
                                   (e.g., O:SPY251219C00650000)
                     NOTE: Q.O:* has 1000 contract limit per subscription
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: real-time)

        Returns:
            Status message indicating stream started

        Examples:
            - start_options_stream(["T.O:SPY251219C00650000", "Q.O:SPY251219P00650000"])
              → Stream SPY option trades and quotes
            - start_options_stream(["AM.O:*"])
              → Stream all options minute aggregates (high volume!)
            - start_options_stream(["FMV.O:AAPL250117C00150000"])
              → Stream fair market value for AAPL call option
        """
        try:
            # Get or create connection
            conn = connection_manager.get_connection(
                "options",
                endpoint=endpoint,
                api_key=api_key or os.getenv("POLYGON_API_KEY"),
            )

            # Connect and authenticate
            await conn.connect()

            # Subscribe to channels
            await conn.subscribe(channels)

            return f"""✓ Started options WebSocket stream
Endpoint: {endpoint}
Channels: {", ".join(channels)}
State: {conn.state.value}

Stream is now active. Messages will be delivered as market data arrives.
Use stop_options_stream() to terminate the connection."""

        except Exception as e:
            return f"✗ Failed to start options stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_options_stream() -> str:
        """
        Stop options market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("options")
            await conn.close()
            return "✓ Stopped options WebSocket stream"
        except KeyError:
            return "○ No active options WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop options stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_options_stream_status() -> str:
        """
        Get current status of options WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("options")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active options WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_options_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active options stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["T.O:SPY251219C00650000", "Q.O:AAPL250117P00150000"])
                     NOTE: Q.O:* has 1000 contract limit per subscription

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("options")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to options stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active options stream. Use start_options_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_options_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active options stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["T.O:SPY251219C00650000"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("options")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from options stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active options stream. Use start_options_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_options_subscriptions() -> str:
        """
        List all active subscriptions for options stream.

        Returns:
            List of subscribed channels grouped by type
        """
        try:
            conn = connection_manager.get_connection("options")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status["subscriptions"]:
                prefix = channel.split(".")[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Options Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    "T": "Trades (T.O:*)",
                    "Q": "Quotes (Q.O:*)",
                    "AM": "Minute Aggregates (AM.O:*)",
                    "AS": "Second Aggregates (AS.O:*)",
                    "FMV": "Fair Market Value (FMV.O:*)",
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active options WebSocket connection"
