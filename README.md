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

> [!NOTE]
> This is a maintained fork of the official [Polygon.io MCP Server](https://github.com/polygon-io/mcp_polygon) with extended features and documentation. For the official Polygon.io version, visit the upstream repository.

# Polygon.io MCP Server

 [![GitHub release](https://img.shields.io/github/v/release/ChrisSc/mcp_polygon)](https://github.com/ChrisSc/mcp_polygon/releases) [![Original by Polygon.io](https://img.shields.io/badge/original-Polygon.io-5F5CFF)](https://github.com/polygon-io/mcp_polygon)

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
├── server.py          # Main MCP server - orchestrates tool registration
├── api_wrapper.py     # Centralized API error handling and response formatting
├── formatters.py      # CSV output formatting utilities
├── validation.py      # Shared validation functions (date validation, future date prevention)
└── tools/             # Tool implementations
    ├── rest/          # 81 REST API tools
    │   ├── stocks.py      # Stock market tools (47 tools)
    │   ├── futures.py     # Futures market tools (11 tools)
    │   ├── crypto.py      # Cryptocurrency tools (7 tools)
    │   ├── forex.py       # Forex market tools (6 tools)
    │   ├── options.py     # Options market tools (9 tools)
    │   ├── indices.py     # Market indices tools (5 tools)
    │   └── economy.py     # Economic indicators (3 tools)
    └── websockets/    # 36 WebSocket streaming tools
        ├── connection_manager.py  # Connection lifecycle and management
        ├── stream_formatter.py    # JSON message formatting
        ├── stocks.py              # Stock streaming (6 tools)
        ├── crypto.py              # Crypto streaming (6 tools)
        ├── options.py             # Options streaming (6 tools)
        ├── futures.py             # Futures streaming (6 tools)
        ├── forex.py               # Forex streaming (6 tools)
        └── indices.py             # Indices streaming (6 tools)
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

### Core Documentation (Root)
- **[CLAUDE.md](CLAUDE.md)** - Project instructions for Claude Code (development guide)
- **[SECURITY.md](SECURITY.md)** - Security policy and responsible disclosure
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

### Implementation Guides (docs/)
- **[Implementation Roadmap](docs/IMPLEMENTATION.md)** - REST API implementation phases (99% coverage, 81 tools)
- **[WebSocket Implementation](docs/WEBSOCKETS_IMPLEMENTATION.md)** - Real-time streaming architecture (36 tools)
- **[Endpoint Patterns](docs/ENDPOINT_PATTERNS.md)** - Tool-to-endpoint mapping (1:1.14 coverage efficiency)
- **[Testing Guide](docs/TESTING.md)** - Test suite documentation (336 tests, 91% coverage)

### Archives
- **[analysis/](analysis/)** - Phase 1-3 documentation archives

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

#### Option 1: STDIO Transport (Direct Installation)

Use the following command to add the Polygon MCP server to your local environment.
This assumes `uvx` is in your $PATH; if not, then you need to provide the full
path to `uvx`.

```bash
# Claude CLI - STDIO transport
claude mcp add polygon -e POLYGON_API_KEY=your_api_key_here -- uvx --from git+https://github.com/ChrisSc/mcp_polygon@v1.0.0 mcp_polygon
```

#### Option 2: HTTP Transport (Docker)

To connect Claude Code to a local Docker HTTP server:

1. **Start the Docker server** (see [Docker HTTP Transport](#docker-http-transport)):
   ```bash
   docker-compose up -d
   ```

2. **Add the server to Claude Code**:
   ```bash
   # Claude CLI - HTTP transport
   claude mcp add polygon-docker http://localhost:8000/mcp --transport http -s user
   ```

The `-s user` flag installs it globally across all projects. Use `-s project` for project-only scope.

**To start Claude Code**, run `claude` in your terminal.
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
                "git+https://github.com/ChrisSc/mcp_polygon@v1.0.0",
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

### Claude Desktop HTTP Configuration

To connect Claude Desktop to a local Docker HTTP server instead of using the stdio transport:

1. **Start the Docker server** (as shown in [Docker HTTP Transport](#docker-http-transport)):
   ```bash
   docker-compose up -d
   ```

2. **Update your `claude_desktop_config.json`** with the HTTP transport configuration:

   A ready-to-use configuration file is provided in [`claude_desktop_config_http.json`](./claude_desktop_config_http.json).

<details>
  <summary>claude_desktop_config.json (HTTP Transport)</summary>

```json
{
    "mcpServers": {
        "polygon-docker": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable-http"
        }
    }
}
```

**Configuration File Locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Important Notes:**
- The `url` field points to your local Docker server endpoint
- The `transport` field must be set to `"streamable-http"`
- No `command`, `args`, or `env` fields are needed for HTTP transport
- The Docker server must be running before starting Claude Desktop
- API key is configured in Docker via `.env` file (not in Claude Desktop config)

**Advantages of HTTP Transport:**
- ✅ Server runs independently of Claude Desktop
- ✅ Can connect multiple MCP clients to the same server
- ✅ Easier debugging with Docker logs
- ✅ Better isolation and resource management

**Disadvantages:**
- ❌ Requires Docker to be running
- ❌ Extra step to start/stop the server
- ❌ Network overhead (minimal for localhost)

For stdio transport (default), see the [Claude Desktop](#claude-desktop) section above.

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

### Docker HTTP Transport

To run the server in Docker with HTTP transport (tested and verified ✅):

```bash
# Start the server
docker-compose up --build

# The server will be available at:
# http://localhost:8000/mcp
```

**Endpoint Details:**
- **URL**: `http://localhost:8000/mcp`
- **Transport**: `streamable-http` (Server-Sent Events)
- **Protocol**: MCP v2024-11-05
- **Tools**: 81 tools across 7 asset classes

**Testing the Endpoint:**

The streamable-http transport requires specific headers:
```bash
# Test with proper headers
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

**Configuration:**

The default `docker-compose.yml` configuration:
- ✅ Runs with `streamable-http` transport
- ✅ Binds to `0.0.0.0:8000` inside container, exposed as `localhost:8000` on host (secure)
- ✅ Includes DNS rebinding protection (MCP spec compliant)
- ✅ Container hardened with read-only filesystem and dropped capabilities
- ✅ Cache directory support for uv package manager

Environment variables control the transport configuration:
- `MCP_TRANSPORT=streamable-http` - Transport type (stdio, sse, or streamable-http)
- `FASTMCP_HOST=0.0.0.0` - Bind address inside container (required for Docker accessibility)
- `FASTMCP_PORT=8000` - Port number

See `.env.example` for all configuration options.

**Connecting MCP Clients:**

- **Claude Code**: See [Claude Code - Option 2: HTTP Transport](#option-2-http-transport-docker) for the CLI command
- **Claude Desktop**: See [Claude Desktop HTTP Configuration](#claude-desktop-http-configuration) for JSON configuration

## Security Considerations

⚠️ **IMPORTANT**: When running with HTTP transports (SSE or streamable-http), ensure proper security measures:

### For Local Development (Docker)

1. **Localhost Binding** (Default Configuration):
   ```yaml
   ports:
     - "127.0.0.1:8000:8000"  # ✅ Safe - localhost only
     # NOT "0.0.0.0:8000:8000"  # ❌ Dangerous - exposes to network
   ```

2. **DNS Rebinding Protection** (Enabled by Default):
   The server automatically enables Origin header validation per MCP specification. Configuration in `server.py`:
   ```python
   transport_security = TransportSecuritySettings(
       enable_dns_rebinding_protection=True,
       allowed_hosts=["localhost:8000", "127.0.0.1:8000"],
       allowed_origins=["http://localhost:8000"],
   )
   ```

3. **API Key Protection**:
   - Never commit API keys to version control
   - Use `.env` files (included in `.gitignore`)
   - Consider Docker secrets for sensitive deployments
   - Monitor API usage at [polygon.io dashboard](https://polygon.io/dashboard)

4. **Container Hardening** (Enabled by Default):
   - Read-only filesystem
   - No new privileges
   - Dropped Linux capabilities
   - See `docker-compose.yml` for full configuration

### Security Level

- **Current Docker Setup**: 8/10 (Production-ready for local development)
- **Localhost binding**: Prevents network exposure
- **DNS rebinding protection**: MCP spec compliant
- **Container hardening**: Defense-in-depth security

For detailed security information, see [SECURITY.md](SECURITY.md).

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

For a complete list of available tools and their parameters, run the MCP Inspector or see the [Endpoint Patterns](docs/ENDPOINT_PATTERNS.md) documentation.

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
- **Data Handling**: This server is a stateless proxy - no user data or API keys are stored, logged, or cached. All requests are forwarded directly to Polygon.io's API.
- **API Key Storage**: Your POLYGON_API_KEY is stored only in your local environment variables. It is never transmitted except to Polygon.io for authentication.
- **Fork Relationship**: This repository (ChrisSc/mcp_polygon) is a fork of polygon-io/mcp_polygon. For Polygon.io's data policies, see their privacy policy above.

## Fork Information

This is a maintained fork of the official [Polygon.io MCP Server](https://github.com/polygon-io/mcp_polygon).

**Fork Maintainer**: Chris Scragg (@ChrisSc)
**Fork Repository**: https://github.com/ChrisSc/mcp_polygon
**Original Author**: Polygon.io

### Why This Fork?

This fork provides:
- Extended development and maintenance beyond the original scope
- Additional documentation and implementation guides (CLAUDE.md, [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md), [docs/ENDPOINT_PATTERNS.md](docs/ENDPOINT_PATTERNS.md), [docs/TESTING.md](docs/TESTING.md))
- Production-ready deployment (Phase 3 complete: 99% API coverage, 81 tools)
- Comprehensive development guides for contributors

For the upstream Polygon.io version, see: https://github.com/polygon-io/mcp_polygon

### Getting Support

- **For fork-specific issues**: Open an issue at [ChrisSc/mcp_polygon](https://github.com/ChrisSc/mcp_polygon/issues)
- **For Polygon.io API questions**: Contact support@polygon.io or visit [Polygon.io Documentation](https://polygon.io/docs)

## Credits

This MCP server was originally created by [Polygon.io](https://polygon.io) and is maintained as a fork by Chris Scragg (@ChrisSc).

**Original Repository**: https://github.com/polygon-io/mcp_polygon
**Original Authors**: Polygon.io team
**Fork Maintainer**: Chris Scragg (@ChrisSc)
**Contact**: clscragg@protonmail.com

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Original Copyright**: Copyright (c) 2025 Polygon.io
**Derivative Work**: This fork maintains the same MIT License

## Contributing

This is a fork of the original Polygon.io MCP Server. Contributions are welcome!

### How to Contribute

1. **Fork-specific improvements**: Open an issue or PR at [ChrisSc/mcp_polygon](https://github.com/ChrisSc/mcp_polygon)
2. **Upstream contributions**: Consider submitting to [polygon-io/mcp_polygon](https://github.com/polygon-io/mcp_polygon) if the change benefits the original project

### Guidelines

- Open an issue before starting work on major features
- Include tests for new functionality
- Follow the existing code style (run `just lint`)
- Update documentation to reflect your changes

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

**Response Time**: Best effort, typically within 1-2 weeks for issues/PRs.

<!----------------------------------------------------------------------------->
[Link]: https://polygon.io/?utm_campaign=mcp&utm_medium=referral&utm_source=github 'Polygon.io Home Page'
<!---------------------------------[ Buttons ]--------------------------------->
[Button]: https://img.shields.io/badge/Get_One_For_Free-5F5CFF?style=for-the-badge&logoColor=white
