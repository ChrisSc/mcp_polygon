<a href="https://polygon.io">
  <div align="center">
    <picture>
        <source media="(prefers-color-scheme: light)" srcset="assets/polygon_banner_lightmode.png">
        <source media="(prefers-color-scheme: dark)" srcset="assets/polygon_banner_darkmode.png">
        <img alt="Polygon.io logo" src="assets/polygon_banner_lightmode.png" height="100">
    </picture>
  </div>
</a>
<br>

> [!IMPORTANT]
> :test_tube: This project is experimental and could be subject to breaking changes.

# Polygon.io MCP Server

 [![GitHub release](https://img.shields.io/github/v/release/polygon-io/mcp_polygon)](https://github.com/polygon-io/mcp_polygon/releases)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides access to [Polygon.io](https://polygon.io?utm_campaign=mcp&utm_medium=referral&utm_source=github) financial market data API through an LLM-friendly interface.

## Overview

This server exposes all Polygon.io API endpoints as MCP tools, providing access to comprehensive financial market data including:

- Stock, options, forex, and crypto aggregates and bars
- Real-time and historical trades and quotes
- Market snapshots
- Ticker details and reference data
- Dividends and splits data
- Financial fundamentals
- Market status and holidays

## Architecture

The MCP server is organized into a modular architecture for scalability and maintainability:

### Project Structure

```
src/mcp_polygon/
├── server.py          # Main MCP server (49 lines) - orchestrates tool registration
├── api_wrapper.py     # Centralized API error handling and response formatting
├── formatters.py      # CSV output formatting utilities
└── tools/             # Tool implementations by asset class
    ├── stocks.py      # Stock market tools (42 tools)
    ├── futures.py     # Futures market tools (11 tools)
    ├── crypto.py      # Cryptocurrency tools (6 tools)
    ├── forex.py       # Forex market tools (6 tools)
    ├── options.py     # Options market tools (8 tools)
    ├── indices.py     # Market indices tools (5 tools)
    └── economy.py     # Economic indicators (3 tools)
```

### Tool Distribution

| Asset Class | Tools | Coverage | Status |
|-------------|-------|----------|--------|
| **Stocks** | 42 | 100% | ✅ Complete |
| **Futures** | 11 | 100% | ✅ Complete |
| **Crypto** | 6 | 100% | ✅ Complete |
| **Forex** | 6 | 100% | ✅ Complete |
| **Options** | 8 | 100% | ✅ Complete |
| **Indices** | 5 | 100% | ✅ Complete |
| **Economy** | 3 | 100% | ✅ Complete |
| **Total** | **81** | **99%** | ✅ Production Ready |

### Implementation Status

- ✅ **Phase 1 Complete** (53 tools): Core market data, aggregates, trades, quotes, snapshots
- ✅ **Phase 2 Complete** (27 tools): Enhanced options, technical indicators, indices, corporate actions
- ✅ **Phase 3 Complete** (1 tool): Inflation expectations tool added, comprehensive endpoint coverage analysis revealing 99% API coverage through generic tool architecture (81 tools serving 92 of 93 REST endpoints)

## Documentation

Comprehensive documentation is available:

- **[CLAUDE.md](CLAUDE.md)** - Project instructions for Claude Code (development guide)
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** - Complete implementation roadmap and phase history
- **[ENDPOINT_PATTERNS.md](ENDPOINT_PATTERNS.md)** - Architecture guide explaining how 81 tools serve 92 endpoints (1:1.14 coverage efficiency)
- **[TESTING.md](TESTING.md)** - Test suite documentation and coverage reports
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

For phase-specific details, see the [analysis/](analysis/) directory containing Phase 1-3 documentation archives.

### Design Principles

- **Modular**: Tools organized by asset class for easy navigation
- **Scalable**: Architecture supports 100+ tools without complexity
- **Type-Safe**: Comprehensive type hints throughout
- **Read-Only**: All tools marked with `readOnlyHint=True` for safety
- **CSV Output**: Token-efficient CSV format for LLM consumption

## Installation

### Prerequisites

- Python 3.10+
- A Polygon.io API key <br> [![Button]][Link]
- [Astral UV](https://docs.astral.sh/uv/getting-started/installation/)
  - For existing installs, check that you have a version that supports the `uvx` command.

### Claude Code
First, install [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)

```bash
npm install -g @anthropic-ai/claude-code
```

Use the following command to add the Polygon MCP server to your local environment.
This assumes `uvx` is in your $PATH; if not, then you need to provide the full
path to `uvx`.

```bash
# Claude CLI
claude mcp add polygon -e POLYGON_API_KEY=your_api_key_here -- uvx --from git+https://github.com/polygon-io/mcp_polygon@v0.5.0 mcp_polygon
```

This command will install the MCP server in your current project.
If you want to install it globally, you can run the command with `-s <scope>` flag.
See `claude mcp add --help` for more options.

To start Claude Code, run `claude` in your terminal.
- If this is your first time using, follow the setup prompts to authenticate

You can also run `claude mcp add-from-claude-desktop` if the MCP server is installed already for Claude Desktop.

### Claude Desktop

1. Follow the [Claude Desktop MCP installation instructions](https://modelcontextprotocol.io/quickstart/user) to complete the initial installation and find your configuration file.
1. Use the following example as reference to add Polygon's MCP server.
Make sure you complete the various fields.
    1. Path find your path to `uvx`, run `which uvx` in your terminal.
    2. Replace `<your_api_key_here>` with your actual Polygon.io API key.
    3. Replace `<your_home_directory>` with your home directory path, e.g., `/home/username` (Mac/Linux) or `C:\Users\username` (Windows).

<details>
  <summary>claude_desktop_config.json</summary>

```json
{
    "mcpServers": {
        "polygon": {
            "command": "<path_to_your_uvx_install>/uvx",
            "args": [
                "--from",
                "git+https://github.com/polygon-io/mcp_polygon@v0.5.0",
                "mcp_polygon"
            ],
            "env": {
                "POLYGON_API_KEY": "<your_api_key_here>",
                "HOME": "<your_home_directory>"
            }
        }
    }
}
```
</details>

## Transport Configuration

By default, STDIO transport is used.

To configure [SSE](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports#http-with-sse) or [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http), set the `MCP_TRANSPORT` environment variable.

Example:

```bash
MCP_TRANSPORT=streamable-http \
POLYGON_API_KEY=<your_api_key_here> \
uv run entrypoint.py
```

## Usage Examples

Once integrated, you can prompt Claude to access Polygon.io data with efficient defaults:

```
Get the last year of daily prices for AAPL stock
Show me yesterday's trading volume for MSFT
What were the biggest stock market gainers today?
Get me the latest crypto market data for BTC-USD
```

### Efficient Data Retrieval

The server uses optimized default limits to minimize API calls:

```python
# Get 1 year of daily bars in a single API call (252 trading days)
get_aggs("AAPL", 1, "day", "2024-01-01", "2024-12-31", limit=252)

# Get 1 trading day of minute bars in a single call (390 minutes)
get_aggs("AAPL", 1, "minute", "2024-10-15", "2024-10-15", limit=390)

# Get full options chain for liquid underlying (500+ contracts)
list_options_contracts("AAPL", contract_type="call", expiration_date="2025-01-17", limit=500)
```

Default limits are set based on typical use cases:
- Aggregates/tick data: 100 records
- Large catalogs: 250 records
- Technical indicators: 50 periods
- Economic data: 10 records

Adjust the `limit` parameter for specific workflows. See [CLAUDE.md](CLAUDE.md) for detailed guidance.

## Available Tools

This MCP server implements **81 production-ready tools** across 7 asset classes:

### Stocks (42 tools)
- **Aggregates**: `get_aggs`, `list_aggs`, `get_grouped_daily_aggs`, `get_daily_open_close_agg`, `get_previous_close_agg`
- **Trades & Quotes**: `list_trades`, `get_last_trade`, `list_quotes`, `get_last_quote`
- **Snapshots**: `list_universal_snapshots`, `get_snapshot_all`, `get_snapshot_ticker`, `get_snapshot_direction`
- **Reference Data**: `list_tickers`, `get_ticker_details`, `list_ticker_news`, `get_ticker_types`, `get_ticker_changes`, `get_related_companies`
- **Corporate Actions**: `list_splits`, `list_dividends`, `list_conditions`, `get_exchanges`, `list_ticker_events`
- **Financials**: `list_stock_financials`, `list_ipos`, `list_short_interest`, `list_short_volume`
- **Market Operations**: `get_market_status`, `get_market_holidays`
- **Analyst Data**: `list_benzinga_analyst_insights`, `list_benzinga_analysts`, `list_benzinga_consensus_ratings`, `list_benzinga_earnings`, `list_benzinga_firms`, `list_benzinga_guidance`, `list_benzinga_news`, `list_benzinga_ratings`
- **Technical Indicators**: `get_sma`, `get_ema`, `get_macd`, `get_rsi`

### Options (8 tools)
- **Contracts**: `list_options_contracts`, `get_options_contract`, `get_options_chain`
- **Snapshots**: `get_snapshot_option`, `list_snapshot_options_chain`
- **Technical Indicators**: `get_options_sma`, `get_options_ema`, `get_options_macd`, `get_options_rsi`

### Futures (11 tools)
- **Aggregates**: `list_futures_aggregates`
- **Contracts**: `list_futures_contracts`, `get_futures_contract_details`
- **Products**: `list_futures_products`, `get_futures_product_details`
- **Market Data**: `list_futures_quotes`, `list_futures_trades`, `get_futures_snapshot`
- **Reference**: `list_futures_schedules`, `list_futures_market_statuses`, `get_futures_snapshot_all`

### Crypto (6 tools)
- **Market Data**: `get_last_crypto_trade`, `get_snapshot_crypto_book`
- **Aggregates**: `get_crypto_aggs`, `list_crypto_aggs`, `get_crypto_daily_open_close_agg`
- **Technical Indicators**: `get_crypto_sma`, `get_crypto_ema`

### Forex (6 tools)
- **Quotes**: `get_last_forex_quote`, `get_real_time_currency_conversion`
- **Aggregates**: `get_forex_aggs`, `list_forex_aggs`, `get_forex_daily_open_close_agg`
- **Technical Indicators**: `get_forex_sma`, `get_forex_ema`

### Indices (5 tools)
- **Snapshots**: `get_indices_snapshot`
- **Technical Indicators**: `get_index_sma`, `get_index_ema`, `get_index_macd`, `get_index_rsi`

### Economy (3 tools)
- **Indicators**: `list_treasury_yields`, `list_inflation`, `list_inflation_expectations`

For a complete list of available tools and their parameters, run the MCP Inspector or see the [ENDPOINT_PATTERNS.md](ENDPOINT_PATTERNS.md) documentation.

Each tool follows the Polygon.io SDK parameter structure while converting responses to CSV format for token-efficient LLM processing.

## Development

### Running Locally

Check to ensure you have the [Prerequisites](#prerequisites) installed.

```bash
# Sync dependencies
uv sync

# Run the server
POLYGON_API_KEY=your_api_key_here uv run mcp_polygon
```

<details>
  <summary>Local Dev Config for claude_desktop_config.json</summary>

```json

  "mcpServers": {
    "polygon": {
      "command": "/your/path/.cargo/bin/uv",
      "args": [
        "run",
        "--with",
        "/your/path/mcp_polygon",
        "mcp_polygon"
      ],
      "env": {
        "POLYGON_API_KEY": "your_api_key_here",
        "HOME": "/Users/danny"
      }
    }
  }
```
</details>

### Debugging

For debugging and testing, we recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon
```

This will launch a browser interface where you can interact with your MCP server directly and see input/output for each tool.

### Code Linting

This project uses [just](https://github.com/casey/just) for common development tasks. To lint your code before submitting a PR:

```bash
just lint
```

This will run `ruff format` and `ruff check --fix` to automatically format your code and fix linting issues.

## Links
- [Polygon.io Documentation](https://polygon.io/docs?utm_campaign=mcp&utm_medium=referral&utm_source=github)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## Privacy Policy

This MCP server interacts with Polygon.io's API to fetch market data. All data requests are subject to Polygon.io's privacy policy and terms of service.

- **Polygon.io Privacy Policy**: https://polygon.io/legal/privacy
- **Data Handling**: This server does not store or cache any user data. All requests are proxied directly to Polygon.io's API.
- **API Key**: Your Polygon.io API key is used only for authenticating requests to their API.

## Contributing
If you found a bug or have an idea for a new feature, please first discuss it with us by submitting a new issue.
We will respond to issues within at most 3 weeks.
We're also open to volunteers if you want to submit a PR for any open issues but please discuss it with us beforehand.
PRs that aren't linked to an existing issue or discussed with us ahead of time will generally be declined.

<!----------------------------------------------------------------------------->
[Link]: https://polygon.io/?utm_campaign=mcp&utm_medium=referral&utm_source=github 'Polygon.io Home Page'
<!---------------------------------[ Buttons ]--------------------------------->
[Button]: https://img.shields.io/badge/Get_One_For_Free-5F5CFF?style=for-the-badge&logoColor=white
