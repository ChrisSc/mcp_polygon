"""
WebSocket streaming tools for crypto market.

Crypto markets operate 24/7 with continuous trading across global exchanges.

Documentation References:
- Connection Guide: polygon-docs/websockets/quickstart.md:65-103
- Authentication: polygon-docs/websockets/quickstart.md:146-175
- Crypto Overview: polygon-docs/websockets/crypto/overview.md:90-117
- Trades Channel (XT.*): polygon-docs/websockets/crypto/trades.md
- Quotes Channel (XQ.*): polygon-docs/websockets/crypto/quotes.md
- Minute Agg (XA.*): polygon-docs/websockets/crypto/aggregates-per-minute.md
- Second Agg (XAS.*): polygon-docs/websockets/crypto/aggregates-per-second.md
- Fair Market Value (FMV.*): polygon-docs/websockets/crypto/fair-market-value.md
"""

import os
from typing import List, Optional
from mcp.types import ToolAnnotations
from .connection_manager import ConnectionManager
from .stream_formatter import format_connection_status


def register_tools(mcp, connection_manager: ConnectionManager):
    """
    Register WebSocket streaming tools for crypto market.

    Args:
        mcp: FastMCP instance
        connection_manager: Global ConnectionManager instance
    """

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def start_crypto_stream(
        channels: Optional[List[str]] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> str:
        """
        Start real-time cryptocurrency market data stream.

        Crypto markets trade 24/7 across global exchanges. Use this to stream
        trades, quotes, and aggregates for crypto pairs like BTC-USD, ETH-USD.

        Documentation References:
        - Connection: polygon-docs/websockets/quickstart.md:65-103
        - Authentication: polygon-docs/websockets/quickstart.md:146-175
        - Crypto Overview: polygon-docs/websockets/crypto/overview.md:90-117
        - Trades Channel (XT.*): polygon-docs/websockets/crypto/trades.md
        - Quotes Channel (XQ.*): polygon-docs/websockets/crypto/quotes.md
        - Minute Agg (XA.*): polygon-docs/websockets/crypto/aggregates-per-minute.md
        - Second Agg (XAS.*): polygon-docs/websockets/crypto/aggregates-per-second.md
        - FMV (FMV.*): polygon-docs/websockets/crypto/fair-market-value.md

        Args:
            channels: List of channels to subscribe. Format: "CHANNEL.SYMBOL"
                     Examples: ["XT.BTC-USD", "XQ.ETH-USD", "XA.*"]
                     Prefixes: XT (trades), XQ (quotes), XA (minute agg),
                              XAS (second agg), FMV (fair value)
                     Symbol format: FROM-TO (e.g., BTC-USD, ETH-USD)
            api_key: Polygon API key (uses POLYGON_API_KEY env if not provided)
            endpoint: WebSocket endpoint (default: wss://socket.polygon.io/crypto)

        Returns:
            Status message indicating stream started

        Examples:
            Start streaming with specific channels:
            >>> await start_crypto_stream(channels=["XT.BTC-USD", "XQ.ETH-USD"])

            Subscribe to all BTC trades:
            >>> await start_crypto_stream(channels=["XT.BTC-USD", "XT.BTC-EUR"])

            Stream minute aggregates for major pairs:
            >>> await start_crypto_stream(channels=["XA.BTC-USD", "XA.ETH-USD"])
        """
        try:
            # Default endpoint for crypto
            if endpoint is None:
                endpoint = "wss://socket.polygon.io/crypto"

            # Default channels if none provided
            if channels is None:
                channels = []

            # Get or create connection
            conn = connection_manager.get_connection(
                "crypto",
                endpoint=endpoint,
                api_key=api_key or os.getenv("POLYGON_API_KEY"),
            )

            # Connect and authenticate
            await conn.connect()

            # Subscribe to channels if provided
            if channels:
                await conn.subscribe(channels)

            return f"""✓ Started crypto WebSocket stream
Endpoint: {endpoint}
Channels: {", ".join(channels) if channels else "None (use subscribe_crypto_channels to add)"}
State: {conn.state.value}

Stream is now active. Messages will be delivered as market data arrives.
Use stop_crypto_stream() to terminate the connection."""

        except Exception as e:
            return f"✗ Failed to start crypto stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def stop_crypto_stream() -> str:
        """
        Stop cryptocurrency market data stream.

        Documentation: polygon-docs/websockets/quickstart.md:570-575

        Returns:
            Status message indicating stream stopped
        """
        try:
            conn = connection_manager.get_connection("crypto")
            await conn.close()
            return "✓ Stopped crypto WebSocket stream"
        except KeyError:
            return "○ No active crypto WebSocket connection"
        except Exception as e:
            return f"✗ Failed to stop crypto stream: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def get_crypto_stream_status() -> str:
        """
        Get current status of crypto WebSocket connection.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:479-490

        Returns:
            Connection status including state, subscriptions, and channel count
        """
        try:
            conn = connection_manager.get_connection("crypto")
            status = conn.get_status()
            return format_connection_status(status)
        except KeyError:
            return "○ No active crypto WebSocket connection"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def subscribe_crypto_channels(channels: List[str]) -> str:
        """
        Add subscriptions to active crypto stream.

        Documentation: polygon-docs/websockets/quickstart.md:245-278

        Args:
            channels: List of channels to add (e.g., ["XT.BTC-USD", "XQ.ETH-USD"])
                     Format: "PREFIX.FROM-TO"
                     Examples: XT.BTC-USD, XQ.ETH-USD, XA.DOGE-USD

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("crypto")
            await conn.subscribe(channels)

            status = conn.get_status()
            return f"""✓ Added {len(channels)} subscriptions to crypto stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active crypto stream. Use start_crypto_stream() first."
        except Exception as e:
            return f"✗ Failed to subscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
    async def unsubscribe_crypto_channels(channels: List[str]) -> str:
        """
        Remove subscriptions from active crypto stream.

        Documentation: polygon-docs/websockets/INDEX_AGENT.md:116-119

        Args:
            channels: List of channels to remove (e.g., ["XT.BTC-USD"])

        Returns:
            Confirmation message with updated subscription list
        """
        try:
            conn = connection_manager.get_connection("crypto")
            await conn.unsubscribe(channels)

            status = conn.get_status()
            return f"""✓ Removed {len(channels)} subscriptions from crypto stream
Total subscriptions: {status["subscription_count"]}
Channels: {", ".join(status["subscriptions"][:10])}{"..." if len(status["subscriptions"]) > 10 else ""}"""
        except KeyError:
            return "✗ No active crypto stream. Use start_crypto_stream() first."
        except Exception as e:
            return f"✗ Failed to unsubscribe: {str(e)}"

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def list_crypto_subscriptions() -> str:
        """
        List all active subscriptions for crypto stream.

        Groups channels by type (trades, quotes, aggregates, fair value) and
        displays symbols within each group.

        Returns:
            List of subscribed channels grouped by type
        """
        try:
            conn = connection_manager.get_connection("crypto")
            status = conn.get_status()

            if not status["subscriptions"]:
                return "No active subscriptions"

            channels_by_type = {}
            for channel in status["subscriptions"]:
                prefix = channel.split(".")[0]
                if prefix not in channels_by_type:
                    channels_by_type[prefix] = []
                channels_by_type[prefix].append(channel)

            output = f"Crypto Stream Subscriptions ({status['subscription_count']} total):\n\n"
            for prefix, channels in sorted(channels_by_type.items()):
                channel_name = {
                    "XT": "Trades",
                    "XQ": "Quotes",
                    "XA": "Minute Aggregates",
                    "XAS": "Second Aggregates",
                    "FMV": "Fair Market Value",
                }.get(prefix, prefix)

                output += f"{channel_name} ({len(channels)}):\n"
                output += "  " + ", ".join(channels[:20])
                if len(channels) > 20:
                    output += f" ... and {len(channels) - 20} more"
                output += "\n\n"

            return output.strip()

        except KeyError:
            return "No active crypto WebSocket connection"
