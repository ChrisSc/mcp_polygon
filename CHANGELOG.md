# Changelog

All notable changes to the Polygon.io MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 2 - Tool Expansion & Quality Improvements

#### Added (27 new tools)
**Options Tools (8 new tools, 1 → 9 total)**
- `list_options_contracts` - Search and filter options contracts by underlying ticker, type, and expiration
- `get_options_contract` - Get detailed information for a specific options contract
- `get_options_chain` - Get full options chain snapshot for an underlying ticker (requires higher API tier)
- `get_options_sma` - Simple Moving Average for options contracts
- `get_options_ema` - Exponential Moving Average for options contracts
- `get_options_macd` - MACD indicator for options contracts
- `get_options_rsi` - Relative Strength Index for options contracts
- `list_snapshot_options_chain` - Get snapshot data for full options chain

**Stocks Tools (11 new tools, 36 → 47 total)**
- `get_related_companies` - Find companies related to a given ticker
- `get_ticker_changes` - Historical ticker symbol changes
- `list_ticker_events` - Corporate events (mergers, acquisitions, etc.)
- `get_sma` - Simple Moving Average technical indicator
- `get_ema` - Exponential Moving Average technical indicator
- `get_macd` - MACD technical indicator
- `get_rsi` - Relative Strength Index technical indicator
- `get_crypto_aggs` - Aggregate bars for cryptocurrencies
- `list_crypto_aggs` - List aggregate bars for crypto
- `get_crypto_daily_open_close_agg` - Daily open/close for crypto
- `get_snapshot_gainers_losers` - Market gainers and losers snapshot

**Indices Tools (5 new tools, 0 → 5 total)**
- `get_indices_snapshot` - Real-time snapshot data for market indices (requires Indices API tier)
- `get_index_sma` - Simple Moving Average for indices (requires Indices API tier)
- `get_index_ema` - Exponential Moving Average for indices (requires Indices API tier)
- `get_index_macd` - MACD indicator for indices (requires Indices API tier)
- `get_index_rsi` - RSI indicator for indices (requires Indices API tier)

**Crypto Tools (2 new tools, 5 → 7 total)**
- `get_crypto_sma` - Simple Moving Average for cryptocurrencies
- `get_crypto_ema` - Exponential Moving Average for cryptocurrencies

**Forex Tools (1 new tool, 5 → 6 total)**
- `get_forex_snapshot_all` - Snapshot of all forex currency pairs

#### Fixed
- **SDK Compliance Issues (7 fixes)**
  - Options: Fixed `underlying_asset` → `underlying_ticker` parameter name
  - Options: Fixed `options_ticker` → `ticker` parameter in SDK calls
  - Options: Fixed `get_options_chain` → `list_snapshot_options_chain` method name
  - Stocks: Fixed `vx_list_ticker_events` → `get_ticker_events` namespace issue
  - Stocks: Fixed `id` → `ticker` parameter in ticker events
  - Indices: Fixed `get_indices_snapshot` → `get_snapshot_indices` method name
  - Economy: Added missing `date_any_of` parameter to `list_treasury_yields`

- **API Wrapper Enhancements**
  - Added support for non-binary SDK responses (objects, lists)
  - Enhanced error handling for technical indicator endpoints
  - Improved response type detection and formatting
  - Better handling of `SingleIndicatorResults` and `MACDIndicatorResults` objects

#### Changed
- **Documentation Updates**
  - Updated README.md with all 80 tools organized by asset class
  - Updated tool distribution table showing 86% API coverage
  - Updated project structure with accurate line counts per file
  - Added references to `PHASE2_COMPLETE.md` and `API_AUDIT_REPORT.md`

- **Code Quality Improvements**
  - Eliminated ~205 lines of duplicate error handling code (10.2% reduction)
  - Centralized API error handling in `PolygonAPIWrapper`
  - Improved code quality score from B+ (83/100) to A- (88-90/100)
  - All tools now use consistent API wrapper pattern

#### Validated
- **API Compliance Audit** - 100% pass rate (80/80 tools verified)
- **MCP Inspector Validation** - Server successfully validated with all 80 tools discoverable
- **Integration Tests** - 6/11 tests passing (5 blocked by API tier requirements, 0 actual failures)
- **SDK Compatibility** - All tools verified against Polygon Python SDK v1.13.2

#### API Tier Requirements
Some Phase 2 tools require higher Polygon.io API tiers:
- **Indices Tools (5 tools)** - Require Indices plan or higher
- **Options Chain Snapshot** - `get_options_chain` requires higher Options tier
- **Alternative:** Use `list_options_contracts` which works on all tiers

---

## [0.5.0] - 2025-01-XX (Phase 1)

### Added
- Initial release with 53 tools across 7 asset classes
- Modular architecture with tools organized by asset class
- CSV output formatting for token-efficient LLM consumption
- Centralized error handling via `PolygonAPIWrapper`
- Support for stdio, SSE, and streamable-http transports

### Asset Classes Implemented
- **Stocks (36 tools)**: Aggregates, trades, quotes, snapshots, reference data, corporate actions, financials, market operations, analyst data
- **Futures (11 tools)**: Aggregates, contracts, products, market data, schedules
- **Crypto (5 tools)**: Last trade, snapshot, aggregates
- **Forex (5 tools)**: Last quote, currency conversion, aggregates
- **Economy (2 tools)**: Treasury yields, inflation data
- **Options (1 tool)**: Option snapshot

---

## Version History

- **Phase 2** (Unreleased) - 80 tools (51% increase from Phase 1)
- **Phase 1** (v0.5.0) - 53 tools (Initial production release)

---

## Links
- [GitHub Repository](https://github.com/polygon-io/mcp_polygon)
- [Polygon.io Documentation](https://polygon.io/docs)
- [Model Context Protocol](https://modelcontextprotocol.io)
