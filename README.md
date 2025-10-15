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
├── server.py          # Main MCP server (38 lines) - orchestrates tool registration
├── formatters.py      # CSV output formatting utilities
└── tools/             # Tool implementations by asset class
    ├── stocks.py      # Stock market tools (36 tools)
    ├── futures.py     # Futures market tools (11 tools)
    ├── crypto.py      # Cryptocurrency tools (2 tools)
    ├── forex.py       # Forex market tools (2 tools)
    ├── economy.py     # Economic indicators (2 tools)
    ├── options.py     # Options market tools (1 tool)
    └── indices.py     # Market indices tools (coming in Phase 2)
```

### Tool Distribution

| Asset Class | Tools | Coverage | Priority |
|-------------|-------|----------|----------|
| **Stocks** | 36 | 77% | Core |
| **Futures** | 11 | 100% | Complete |
| **Crypto** | 2 | 29% | Phase 2 |
| **Forex** | 2 | 15% | Phase 2 |
| **Economy** | 2 | 67% | Core |
| **Options** | 1 | 4% | Phase 2 |
| **Indices** | 0 | 0% | Phase 2 |
| **Total** | **53** | **57%** | Expanding |

### Current Implementation Status

- **Phase 1 Complete** (53 tools): Core market data, aggregates, trades, quotes, snapshots
- **Phase 2 Planning** (40 tools): Enhanced options coverage, technical indicators, additional endpoints

For detailed architecture documentation, see:
- `IMPLEMENTATION.md` - Complete implementation roadmap
- `PHASE-1.md` - Phase 1 completion report
- `REFACTORING_COMPLETE.md` - Architecture migration guide
- `REST_AUDIT.csv` - Endpoint coverage analysis

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

Once integrated, you can prompt Claude to access Polygon.io data:

```
Get the latest price for AAPL stock
Show me yesterday's trading volume for MSFT
What were the biggest stock market gainers today?
Get me the latest crypto market data for BTC-USD
```

## Available Tools

This MCP server currently implements **53 tools** across 7 asset classes:

### Core Market Data (36 tools)
- **Aggregates**: `get_aggs`, `list_aggs`, `get_grouped_daily_aggs`, `get_daily_open_close_agg`, `get_previous_close_agg`
- **Trades**: `list_trades`, `get_last_trade`
- **Quotes**: `list_quotes`, `get_last_quote`
- **Snapshots**: `list_universal_snapshots`, `get_snapshot_all`, `get_snapshot_ticker`, `get_snapshot_direction`
- **Reference Data**: `list_tickers`, `get_ticker_details`, `list_ticker_news`, `get_ticker_types`
- **Corporate Actions**: `list_splits`, `list_dividends`, `list_conditions`, `get_exchanges`
- **Financials**: `list_stock_financials`, `list_ipos`, `list_short_interest`, `list_short_volume`
- **Market Operations**: `get_market_status`, `get_market_holidays`
- **Analyst Data**: `list_benzinga_analyst_insights`, `list_benzinga_consensus_ratings`, `list_benzinga_earnings`, `list_benzinga_news`, `list_benzinga_ratings`

### Futures (11 tools)
- `list_futures_aggregates`, `list_futures_contracts`, `get_futures_contract_details`
- `list_futures_products`, `get_futures_product_details`
- `list_futures_quotes`, `list_futures_trades`, `list_futures_schedules`
- `list_futures_market_statuses`, `get_futures_snapshot`

### Cryptocurrency (2 tools)
- `get_last_crypto_trade`, `get_snapshot_crypto_book`

### Forex (2 tools)
- `get_real_time_currency_conversion`, `get_last_forex_quote`

### Economy (2 tools)
- `list_treasury_yields`, `list_inflation`

### Options (1 tool)
- `get_snapshot_option`

For a complete list of available tools and their parameters, run the MCP Inspector or see `REST_AUDIT.csv`.

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
