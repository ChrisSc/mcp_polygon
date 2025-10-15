# Performance Optimization Recommendations

**Priority**: Phase 4 Implementation
**Impact**: High (User Experience) + Medium (API Efficiency)
**Effort**: Low (2-4 hours)

---

## Priority 1: Update Default Limits

### Problem Statement

Current default `limit=10` is too conservative:
- Getting 1 day of minute bars (390 records) requires **39 API calls**
- Getting 1 year of daily bars (252 records) requires **25 API calls**
- Users must repeatedly specify higher limits in every call

### Performance Impact

**Minimal**: Converting 100 vs 10 records adds only **~2 ms**
- 10 records: 0.30 ms
- 100 records: 2.30 ms
- Difference: 2.00 ms (negligible)

### User Experience Impact

**High**: Reduces API calls by 10-20x for typical workflows

### Proposed Changes

```python
# Current defaults (BEFORE)
limit: Optional[int] = 10  # Most tools

# Proposed defaults (AFTER)
# Aggregates/bars
limit: Optional[int] = 100  # 1-2 months daily bars, or 2.5 hours minute bars

# Tick data (trades/quotes)
limit: Optional[int] = 100  # Reasonable sample

# Reference data (catalogs)
limit: Optional[int] = 250  # Large listings (already used in options.py)

# Technical indicators
limit: Optional[int] = 50   # Typical indicator window

# Economic data
limit: Optional[int] = 10   # Keep current (sparse data)
```

### Files to Update

#### stocks.py (26 tools)

```python
# Aggregates
async def get_aggs(..., limit: Optional[int] = 100) -> str:
async def get_grouped_daily_aggs(..., limit: Optional[int] = 100) -> str:
async def get_previous_close(..., limit: Optional[int] = 100) -> str:

# Tick data
async def list_trades(..., limit: Optional[int] = 100) -> str:
async def list_quotes(..., limit: Optional[int] = 100) -> str:

# Reference data
async def list_tickers(..., limit: Optional[int] = 250) -> str:
async def get_ticker_details(..., limit: Optional[int] = 100) -> str:
async def get_ticker_news(..., limit: Optional[int] = 100) -> str:

# Technical indicators (10 → 50)
async def get_sma(..., limit: Optional[int] = 50) -> str:
async def get_ema(..., limit: Optional[int] = 50) -> str:
async def get_macd(..., limit: Optional[int] = 50) -> str:
async def get_rsi(..., limit: Optional[int] = 50) -> str:
```

#### futures.py (9 tools)

```python
# Reference data
async def list_futures_contracts(..., limit: Optional[int] = 250) -> str:

# Market data
async def get_futures_aggs(..., limit: Optional[int] = 100) -> str:
async def list_futures_trades(..., limit: Optional[int] = 100) -> str:
async def list_futures_quotes(..., limit: Optional[int] = 100) -> str:
```

#### crypto.py (4 tools)

```python
# Market data
async def get_crypto_aggs(..., limit: Optional[int] = 100) -> str:
async def list_crypto_trades(..., limit: Optional[int] = 100) -> str:

# Technical indicators
async def get_crypto_sma(..., limit: Optional[int] = 50) -> str:
async def get_crypto_ema(..., limit: Optional[int] = 50) -> str:
async def get_crypto_macd(..., limit: Optional[int] = 50) -> str:
async def get_crypto_rsi(..., limit: Optional[int] = 50) -> str:
```

#### forex.py (4 tools)

```python
# Market data
async def get_forex_aggs(..., limit: Optional[int] = 100) -> str:

# Technical indicators
async def get_forex_sma(..., limit: Optional[int] = 50) -> str:
async def get_forex_ema(..., limit: Optional[int] = 50) -> str:
async def get_forex_macd(..., limit: Optional[int] = 50) -> str:
async def get_forex_rsi(..., limit: Optional[int] = 50) -> str:
```

#### indices.py (5 tools)

```python
# Snapshots
async def get_indices_snapshot(..., limit: Optional[int] = 50) -> str:

# Technical indicators
async def get_index_sma(..., limit: Optional[int] = 50) -> str:
async def get_index_ema(..., limit: Optional[int] = 50) -> str:
async def get_index_macd(..., limit: Optional[int] = 50) -> str:
async def get_index_rsi(..., limit: Optional[int] = 50) -> str:
```

#### options.py (No changes needed)

```python
# Already optimized:
async def list_options_contracts(..., limit: Optional[int] = 100) -> str:
async def get_options_chain(..., limit: Optional[int] = 250) -> str:
# Technical indicators already at 10 (appropriate)
```

#### economy.py (No changes needed)

```python
# Economic data is sparse - limit=10 is appropriate
async def list_treasury_yields(..., limit: Optional[int] = 10) -> str:
async def list_inflation_data(..., limit: Optional[int] = 10) -> str:
async def list_inflation_expectations(..., limit: Optional[int] = 10) -> str:
```

### Total Changes

- **Files**: 5 (stocks.py, futures.py, crypto.py, forex.py, indices.py)
- **Tools**: 48 (out of 81 total)
- **Lines changed**: ~48 (one per tool signature)

### Testing Plan

```bash
# 1. Run all tests to ensure no regressions
pytest tests/ -v

# 2. Verify server loads
python -c "from src.mcp_polygon.server import poly_mcp; print(f'{len(poly_mcp._tool_manager._tools)} tools loaded')"

# 3. Test with MCP Inspector
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon

# 4. Validate specific tools
# - get_aggs with default limit (should return 100 records)
# - Technical indicators (should return 50 records)
# - Options contracts (should still return 100 records)
```

### Documentation Updates

Add to tool docstrings:

```python
async def get_aggs(
    ticker: str,
    multiplier: int,
    timespan: str,
    from_date: Union[str, date],
    to_date: Union[str, date],
    adjusted: Optional[bool] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = 100,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Get aggregate bars (candles) for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        multiplier: Size of timespan multiplier (e.g., 1 for 1 day)
        timespan: Size of time window (day, hour, minute, etc.)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        adjusted: Whether to adjust for splits
        sort: Sort order ('asc' or 'desc')
        limit: Maximum number of results (default: 100, max: 50000)
              Typical usage: 100 for daily bars (1-2 months),
              390 for minute bars (1 trading day),
              252 for annual analysis
        params: Additional API parameters

    Returns:
        CSV-formatted aggregate data
    """
```

### Rollout Plan

#### Phase 1: Update Code (1 hour)
1. Update 48 tool signatures across 5 files
2. Run linter: `just lint`
3. Commit changes: `git commit -m "feat: increase default limits for better UX"`

#### Phase 2: Test (1 hour)
1. Run test suite
2. Manual testing via MCP Inspector
3. Verify tool counts and signatures

#### Phase 3: Update Documentation (1 hour)
1. Update CLAUDE.md with new defaults
2. Update README.md examples
3. Add migration guide for users

#### Phase 4: Deploy (30 minutes)
1. Create PR
2. Review and merge
3. Tag release: `v1.1.0`

### Expected Outcomes

**Before** (limit=10):
```python
# User code to get 1 year of daily bars (252 days)
records = []
for i in range(26):  # 26 API calls!
    batch = get_aggs('AAPL', 1, 'day', f'2024-{i*10+1:02d}-01', ..., limit=10)
    records.extend(batch)
```

**After** (limit=100):
```python
# User code to get 1 year of daily bars (252 days)
records = []
for i in range(3):  # Only 3 API calls
    batch = get_aggs('AAPL', 1, 'day', f'2024-{i*100+1:03d}', ..., limit=100)
    records.extend(batch)

# Or even simpler:
records = get_aggs('AAPL', 1, 'day', '2024-01-01', '2024-12-31', limit=252)
# Single API call!
```

**Impact**:
- 26 calls → 1-3 calls (87-96% reduction)
- Better user experience
- Lower rate limit risk
- Same performance (adds ~2 ms)

---

## Priority 2: Add Limit Guidance to Documentation

### Update CLAUDE.md

Add new section:

```markdown
## Default Limit Guidelines

### Understanding Limits

The `limit` parameter controls how many records are returned per API call. Higher limits reduce the number of API calls needed but may increase response time slightly.

### Default Limits by Tool Type

| Tool Type              | Default Limit | Typical Use Case |
|------------------------|---------------|------------------|
| Aggregates (bars)      | 100           | 1-2 months daily, 2.5 hours minute bars |
| Tick data (trades)     | 100           | Sample of recent activity |
| Reference data         | 250           | Large catalogs (options contracts, tickers) |
| Technical indicators   | 50            | Typical indicator window (20-50 periods) |
| Economic data          | 10            | Sparse historical data |

### When to Increase Limits

- **1 year of daily bars**: Use `limit=252` (trading days)
- **1 day of minute bars**: Use `limit=390` (6.5 hours × 60 min)
- **Full options chain**: Use `limit=500+` for liquid underlyings
- **Historical technical indicators**: Use `limit=252` for annual analysis

### Performance Impact

Increasing limits has minimal performance impact:
- 10 records: ~0.3 ms
- 100 records: ~2.3 ms
- 1000 records: ~23 ms
- 5000 records: ~111 ms

**Recommendation**: Use higher limits to reduce API calls. The performance cost is negligible.
```

### Update README.md Examples

Replace:

```python
# OLD (inefficient)
bars = polygon.get_aggs("AAPL", 1, "day", "2024-01-01", "2024-12-31", limit=10)
# Returns only 10 bars, requires 25 more calls to get full year
```

With:

```python
# NEW (efficient)
bars = polygon.get_aggs("AAPL", 1, "day", "2024-01-01", "2024-12-31", limit=252)
# Returns all 252 trading days in a single call
```

---

## Priority 3: Optional Caching (Phase 5)

### When to Implement

- After Phase 4 (default limits) is complete
- If monitoring shows > 10% of queries are for reference data
- If rate limiting becomes an issue

### What to Cache

| Endpoint | Cache TTL | Cache Key | Benefit |
|----------|-----------|-----------|---------|
| Market holidays | 1 year | `holidays_{year}` | High (static data) |
| Exchanges | 1 month | `exchanges` | Medium (rarely changes) |
| Ticker types | 1 week | `ticker_types` | Medium (rarely changes) |
| Conditions/SIPs | 1 week | `conditions` | Low (rare queries) |

### Implementation Example

```python
# Add to api_wrapper.py
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPIWrapper(PolygonAPIWrapper):
    """Extended wrapper with caching for reference data."""

    def __init__(self, client, formatter, cache_size: int = 256):
        super().__init__(client, formatter)
        self._cache = {}
        self._cache_ttl = {}

    def _is_cacheable(self, method_name: str) -> bool:
        """Determine if endpoint should be cached."""
        cacheable_methods = {
            'get_market_holidays': 365 * 86400,  # 1 year
            'get_exchanges': 30 * 86400,         # 1 month
            'get_ticker_types': 7 * 86400,       # 1 week
        }
        return method_name in cacheable_methods

    async def call(self, method_name: str, **kwargs) -> str:
        """Override call() to add caching logic."""
        # Check cache
        cache_key = f"{method_name}:{hash(frozenset(kwargs.items()))}"

        if cache_key in self._cache:
            if time.time() < self._cache_ttl.get(cache_key, 0):
                logger.debug(f"Cache hit: {method_name}")
                return self._cache[cache_key]

        # Cache miss - call parent
        result = await super().call(method_name, **kwargs)

        # Store in cache if cacheable
        if self._is_cacheable(method_name):
            ttl = self._get_cache_ttl(method_name)
            self._cache[cache_key] = result
            self._cache_ttl[cache_key] = time.time() + ttl
            logger.debug(f"Cached: {method_name} (TTL: {ttl}s)")

        return result
```

### Benefits

- Reduce API calls by 80% for reference data
- Improve response time: 100 ms → 0.1 ms for cached queries
- Lower rate limit risk

### Risks

- Stale data (mitigated by TTL)
- Memory usage (~1 MB for 256 cached items)
- Complexity (adds 50 lines of code)

---

## Summary

### Recommended Actions

| Priority | Action | Impact | Effort | Timeline |
|----------|--------|--------|--------|----------|
| 1 (HIGH) | Update default limits | High (UX) | Low (2h) | Phase 4 |
| 2 (MEDIUM) | Update documentation | Medium (UX) | Low (1h) | Phase 4 |
| 3 (LOW) | Add caching | Low-Medium | Medium (4h) | Phase 5 |

### Expected Outcomes

**Immediate** (Phase 4):
- 10-20x reduction in API calls for typical queries
- Improved user experience (fewer pagination calls needed)
- No performance degradation (adds ~2 ms)

**Long-term** (Phase 5):
- 80% reduction in reference data API calls
- Faster response times for repeated queries
- Lower rate limit risk

### Success Metrics

After Phase 4 implementation, measure:
1. Average API calls per user session (expect: 50-80% reduction)
2. Rate limit errors (expect: 70% reduction)
3. User feedback (expect: positive)
4. Performance benchmarks (expect: < 5 ms increase)

---

**Report End**
