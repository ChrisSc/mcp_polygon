# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that exposes Polygon.io financial market data API through an LLM-friendly interface. The server implements 53 tools across 7 asset classes (stocks, options, futures, crypto, forex, economy, indices) and returns data in CSV format for token efficiency.

**Key Architecture Principle**: Modular design with centralized error handling. Tools are organized by asset class in `src/mcp_polygon/tools/`, all using the `PolygonAPIWrapper` for consistent error handling and response formatting.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (REQUIRED for all operations)
source venv/bin/activate

# Install package in development mode
pip install -e .

# Install dependencies
uv sync
```

### Running the Server
```bash
# Run with API key from environment
POLYGON_API_KEY=your_key uv run mcp_polygon

# Or source .env file
source .env && uv run mcp_polygon

# Run with specific transport (default: stdio)
MCP_TRANSPORT=streamable-http POLYGON_API_KEY=your_key uv run mcp_polygon
```

### Testing
```bash
# Run all tests (activate venv first)
source venv/bin/activate && pytest tests/ -v

# Run specific test file
pytest tests/test_api_wrapper.py -v
pytest tests/test_formatters.py -v

# Run tests with coverage
pytest tests/ --cov=src/mcp_polygon --cov-report=html

# Run MCP Inspector for manual testing
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon
```

### Linting
```bash
# Format and fix all issues (recommended before commits)
just lint

# Individual commands
uv run ruff format
uv run ruff check --fix
```

## Architecture Overview

### API Wrapper Pattern (Phase 2 Refactoring)

All tools now use a centralized `PolygonAPIWrapper` for consistent error handling and response formatting:

```python
def register_tools(mcp, client, formatter):
    """Register all [asset-class]-related tools with the MCP server."""
    from mcp.types import ToolAnnotations
    from ..api_wrapper import PolygonAPIWrapper

    # Create API wrapper instance for this module
    api = PolygonAPIWrapper(client, formatter)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def tool_name(param1: str, param2: Optional[int] = None) -> str:
        """Tool description for LLM."""
        return await api.call(
            "method_name",  # For vx.* methods, use "vx_method_name"
            param1=param1,
            param2=param2,
        )
```

**Benefits of API Wrapper:**
- Eliminates 40% code duplication (removed ~205 lines of boilerplate)
- Centralized error handling with context-aware messages (401, 403, 404, 429, 500, timeouts, connection errors)
- Automatic binary response decoding
- Structured logging for all API calls
- Single source of truth for error messages

### Module Organization

```
src/mcp_polygon/
├── server.py          # Main orchestrator (49 lines)
│                      # - Imports all tool modules
│                      # - Creates FastMCP instance
│                      # - Configures logging
│                      # - Calls register_tools() for each asset class
├── api_wrapper.py     # Centralized API wrapper (170 lines)
│                      # - PolygonAPIWrapper: Handles all API calls
│                      # - PolygonAPIError: Formats error messages
│                      # - Automatic binary decoding & CSV formatting
├── formatters.py      # CSV output utilities (82 lines)
│                      # - json_to_csv(): Main conversion function
│                      # - _flatten_dict(): Nested dict flattening
└── tools/             # Asset class modules
    ├── stocks.py      # 35 tools (1,266 lines)
    ├── futures.py     # 11 tools (330 lines)
    ├── crypto.py      # 2 tools (49 lines)
    ├── forex.py       # 2 tools (55 lines)
    ├── economy.py     # 2 tools (77 lines)
    ├── options.py     # 1 tool (35 lines)
    └── indices.py     # 0 tools (Phase 3)
```

### Error Handling Flow

The `PolygonAPIWrapper` provides automatic error handling:

1. **HTTP Status Codes**:
   - 401: "Invalid API key. Please check your POLYGON_API_KEY environment variable."
   - 403: "API key does not have permission to access {operation}. Upgrade your plan at polygon.io"
   - 404: "Resource not found (ticker=INVALID). Please verify the ticker symbol or parameters."
   - 429: "Rate limit exceeded. Please wait a moment and try again."
   - 500-599: "Polygon API is experiencing issues (status 500). Please try again later."

2. **Connection Errors**: Automatically detects timeout and connection failures with helpful messages

3. **Context-Aware**: Error messages include ticker symbols, currency pairs, or other relevant context

4. **Logging**: All errors logged with full context for debugging (stderr for MCP compatibility)

### CSV Formatter Behavior

The `json_to_csv()` function in `formatters.py`:
1. Accepts JSON string or dict input
2. Extracts `results` array if present, otherwise wraps data in array
3. Flattens nested dictionaries using underscore separator (e.g., `session_open` → `session_open`)
4. Converts lists to comma-separated strings
5. Returns CSV with headers and all unique columns across records

### Polygon SDK Client Usage

The server uses the official `polygon-api-client` SDK:
- `polygon_client = RESTClient(POLYGON_API_KEY)` creates the client
- Most endpoints accessed via `client.method_name()`
- Some endpoints use `client.vx.method_name()` (newer API version)
- All calls use `raw=True` to get binary response data
- Response format: `results.data` contains bytes that are automatically decoded by API wrapper

## Adding New Tools

### Step 1: Choose the Correct Module

Add tools to the appropriate file in `src/mcp_polygon/tools/`:
- Stock market data → `stocks.py`
- Options data → `options.py`
- Futures data → `futures.py`
- Cryptocurrency → `crypto.py`
- Forex/currencies → `forex.py`
- Economic indicators → `economy.py`
- Market indices → `indices.py`

### Step 2: Implement Tool Function

Follow the API wrapper pattern inside the `register_tools()` function:

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def new_tool_name(
    required_param: str,
    optional_param: Optional[int] = None,
    limit: Optional[int] = 10,  # Standard default
    params: Optional[Dict[str, Any]] = None,  # Standard for extra params
) -> str:
    """
    Brief description of what this tool does.

    Use clear, LLM-friendly language explaining the tool's purpose.
    """
    return await api.call(
        "method_name",  # Use "vx_method_name" for vx.* methods
        required_param=required_param,
        optional_param=optional_param,
        limit=limit,
        params=params,
    )
```

**Important Notes:**
- NO try-except needed (handled by API wrapper)
- NO binary decoding needed (handled by API wrapper)
- NO CSV formatting needed (handled by API wrapper)
- For vx methods, prefix with "vx_": `await api.call("vx_list_stock_financials", ...)`

### Step 3: Test the Tool

1. Verify server loads: `source venv/bin/activate && pip install -e . && python -c "from src.mcp_polygon.server import poly_mcp; print(f'✅ {len(poly_mcp._tool_manager._tools)} tools loaded')"`
2. Test with MCP Inspector: `npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon`
3. Add integration test to `tests/test_rest_endpoints.py` if needed

## Testing Strategy

The test suite is organized into:

**tests/test_api_wrapper.py** (24 tests, 100% coverage on wrapper)
- Error formatting (9 tests): HTTP status codes, timeouts, connection errors
- API wrapper functionality (15 tests): successful calls, vx methods, error handling

**tests/test_formatters.py** (28 tests, 100% coverage)
- Dictionary flattening edge cases
- JSON to CSV conversion
- Unicode, special characters, null handling

**tests/test_rest_endpoints.py** (54 tests)
- Server initialization (4 tests)
- Tool signature validation (3 tests)
- CSV formatting integration (6 tests)
- Error handling (2 tests)
- Integration tests (1 test)
- Edge cases (3 tests)

**tests/conftest.py** (pytest fixtures)
- `mock_polygon_client`: Mock REST client with vx attribute
- `mock_response`: Factory for creating mock API responses
- `api_wrapper`: Pre-configured API wrapper for testing
- `sample_aggregate_data`, `sample_trade_data`, `sample_ticker_details`: Test data fixtures

## Common Issues

### ModuleNotFoundError for 'mcp'
**Solution**: Always activate venv first: `source venv/bin/activate && pip install -e .`

### POLYGON_API_KEY not set warning
**Expected behavior**: Server runs without API key for testing. Source `.env` for actual API calls.

### Tools not appearing in MCP client
**Likely cause**: Error during tool registration. Check server logs and verify all imports work:
```bash
python -c "from src.mcp_polygon.server import poly_mcp; print(list(poly_mcp._tool_manager._tools.keys())[:5])"
```

### API wrapper errors not showing context
**Check**: Ensure you're passing relevant parameters (ticker, from_/to for forex) - the wrapper automatically includes them in error messages

## Refactoring History

### Phase 1 (Complete): Modular Architecture
- Refactored monolithic 2,006-line server.py into 7 asset class modules
- Server.py reduced to 38 lines (98% reduction)
- All 53 tools preserved with zero behavioral changes

### Phase 2 (Complete): API Wrapper Pattern
- Created centralized `PolygonAPIWrapper` for error handling
- Refactored all 53 tools to use wrapper pattern
- Eliminated ~205 lines of duplicate code (10.2% reduction)
- Added comprehensive test suite (24 tests, 100% wrapper coverage)
- Improved code quality score from B+ (83/100) to A- (88-90/100)

### Phase 3 (Planned): Module Restructuring
- Split stocks.py into submodules (aggregates, trades_quotes, snapshots, reference, fundamentals, benzinga)
- Target: Keep all modules under 500 lines

### Phase 4 (Planned): Parameter Objects & Testing
- Create parameter objects for functions with 20+ parameters
- Increase test coverage to 70%+
- Comprehensive docstring updates

## Key Implementation Details

### Why CSV Instead of JSON?
CSV is more token-efficient for LLM consumption. A typical JSON response with 100 records might use 50KB, while CSV uses ~15KB for the same data.

### Why All Tools Are Read-Only?
This is a data retrieval service. The `readOnlyHint=True` annotation signals to MCP clients that tools don't modify state, enabling caching and safer autonomous agent usage.

### Why Async Functions?
FastMCP requires all tool functions to be async, even though the Polygon SDK client is synchronous. The async wrapper allows FastMCP to manage concurrency.

### Why Centralized Error Handling?
The API wrapper eliminates code duplication and provides consistent, context-aware error messages across all 53 tools. Errors are automatically logged for debugging.

### Transport Configuration
The server supports three MCP transports via `MCP_TRANSPORT` env var:
- `stdio` (default) - Standard input/output
- `sse` - Server-Sent Events over HTTP
- `streamable-http` - Streamable HTTP (newest)

## Related Resources

- Polygon.io API Docs: https://polygon.io/docs
- MCP Specification: https://modelcontextprotocol.io
- FastMCP SDK: https://github.com/modelcontextprotocol/python-sdk
- Local docs: `polygon-docs/rest/` and `anthropic-docs/modelcontextprotocol/`
- Architecture docs: `REFACTORING_COMPLETE.md`, `PHASE-1.md`, `CODE_REVIEW.md`
