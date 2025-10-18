# Params-Only Method Handling in PolygonAPIWrapper

## Overview

The `PolygonAPIWrapper.call()` method has been enhanced to properly handle SDK methods that require query parameters to be passed via the `params` dict instead of as individual kwargs.

## Problem Statement

Some Polygon SDK methods (e.g., `list_snapshot_options_chain`) only accept query parameters through a `params` dict argument, not as individual kwargs. The SDK method signature is:

```python
list_snapshot_options_chain(
    underlying_asset: str,
    params: Optional[Dict[str, Any]] = None,
    raw: bool = False,
    options: Optional[RequestOptionBuilder] = None
)
```

However, our MCP tools call these methods with individual kwargs like:

```python
api.call(
    "list_snapshot_options_chain",
    underlying_asset="SPY",
    strike_price=450.0,
    contract_type="call",
    limit=50,
)
```

This mismatch caused the SDK to ignore query parameters.

## Solution

The `PolygonAPIWrapper.call()` method now detects params-only methods and intelligently reorganizes kwargs before calling the SDK:

### Implementation Details

1. **Method Detection**: A `PARAMS_ONLY_METHODS` set identifies methods requiring special handling:
   ```python
   PARAMS_ONLY_METHODS = {'list_snapshot_options_chain'}
   ```

2. **Parameter Separation**: For params-only methods, kwargs are split into two categories:
   - **Query parameters** (go in `params` dict): `strike_price`, `expiration_date`, `contract_type`, `limit`, `order`, `sort`
   - **Direct parameters** (passed as kwargs): `underlying_asset`, `raw`, `options`, `params`

3. **None Value Filtering**: Query parameters with `None` values are excluded from the `params` dict to avoid sending empty parameters.

4. **Params Dict Merging**: If a user provides their own `params` dict, it's merged with extracted query parameters.

5. **Backward Compatibility**: Methods not in `PARAMS_ONLY_METHODS` continue to work as before (parameters passed directly).

## Code Example

### Before (Not Working)
```python
# SDK received: list_snapshot_options_chain(underlying_asset="SPY", strike_price=450.0, raw=True)
# SDK ignored: strike_price (not in method signature)
result = await api.call(
    "list_snapshot_options_chain",
    underlying_asset="SPY",
    strike_price=450.0,
    contract_type="call",
)
```

### After (Working)
```python
# SDK receives: list_snapshot_options_chain(
#     underlying_asset="SPY",
#     params={"strike_price": 450.0, "contract_type": "call"},
#     raw=True
# )
result = await api.call(
    "list_snapshot_options_chain",
    underlying_asset="SPY",
    strike_price=450.0,
    contract_type="call",
)
```

## Test Coverage

The implementation includes comprehensive test coverage:

1. **`test_params_only_method_with_query_params`**: Verifies query parameters are correctly moved to `params` dict
2. **`test_params_only_method_with_none_values`**: Ensures None values are excluded from `params` dict
3. **`test_params_only_method_with_all_none_values`**: Confirms `params` dict is omitted when all query params are None
4. **`test_params_only_method_with_existing_params_dict`**: Tests merging of user-provided `params` with extracted query params
5. **`test_params_only_method_does_not_break_other_methods`**: Validates backward compatibility (non-params-only methods unaffected)

All 29 tests in `test_api_wrapper.py` pass, including the 5 new tests.

## Adding New Params-Only Methods

To add a new method to params-only handling:

1. Add the method name to `PARAMS_ONLY_METHODS` set in `api_wrapper.py` (line 144):
   ```python
   PARAMS_ONLY_METHODS = {'list_snapshot_options_chain', 'new_method_name'}
   ```

2. Add query parameter keys to `param_keys` set if they're not already included (line 152-155):
   ```python
   param_keys = {
       'strike_price', 'expiration_date', 'contract_type',
       'limit', 'order', 'sort',
       'new_param_1', 'new_param_2'  # Add new query params here
   }
   ```

3. Add any direct parameters (non-query) to `direct_keys` set if needed (line 158):
   ```python
   direct_keys = {'underlying_asset', 'raw', 'options', 'params', 'new_direct_param'}
   ```

4. Write tests following the patterns in `test_api_wrapper.py` (lines 316-451).

## Files Modified

- `/Users/chris/Projects/mcp_polygon/src/mcp_polygon/api_wrapper.py` (lines 140-180)
- `/Users/chris/Projects/mcp_polygon/tests/test_api_wrapper.py` (lines 316-451, added 5 tests)
- `/Users/chris/Projects/mcp_polygon/tests/test_rest_endpoints.py` (lines 770-777, updated test assertions)

## Performance Impact

The parameter reorganization logic adds negligible overhead:
- Executes only for methods in `PARAMS_ONLY_METHODS` (currently 1 method)
- Simple dict operations (O(n) where n = number of kwargs, typically < 10)
- No impact on other 116 tools

## Maintenance Notes

- **Adding methods**: Update `PARAMS_ONLY_METHODS` set when SDK introduces new params-only methods
- **Query parameters**: Update `param_keys` set if SDK adds new query parameters to existing methods
- **Testing**: Always add corresponding tests when updating the sets
- **Documentation**: Update this document when adding new methods

## Related Documentation

- Polygon SDK Documentation: https://polygon-api-client.readthedocs.io/
- MCP Tool Pattern: See `/Users/chris/Projects/mcp_polygon/CLAUDE.md` (lines 158-191)
- API Wrapper Architecture: See `/Users/chris/Projects/mcp_polygon/docs/IMPLEMENTATION.md`
