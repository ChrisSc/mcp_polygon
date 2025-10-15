# Polygon.io MCP Server - Quick Reference Guide

## File Locations

### Main Files
- **Orchestrator**: `/src/mcp_polygon/server.py` (38 lines)
- **Backup**: `/src/mcp_polygon/server_backup.py` (2,006 lines)
- **Formatters**: `/src/mcp_polygon/formatters.py` (unchanged)

### Tool Modules
All located in `/src/mcp_polygon/tools/`:
- `stocks.py` - 35 tools (stocks, market data, Benzinga)
- `futures.py` - 11 tools (futures contracts, quotes, trades)
- `crypto.py` - 2 tools (crypto trades, order books)
- `forex.py` - 2 tools (currency quotes, conversion)
- `economy.py` - 2 tools (treasury yields, inflation)
- `options.py` - 1 tool (option snapshots)
- `indices.py` - 0 tools (Phase 2 placeholder)

## Tool Counts by Module

```
stocks    → 35 tools
futures   → 11 tools
economy   →  2 tools
forex     →  2 tools
crypto    →  2 tools
options   →  1 tool
indices   →  0 tools (Phase 2)
────────────────────
TOTAL     → 53 tools
```

## How to Add New Tools

### 1. Choose the right module
Based on asset class: stocks, options, futures, crypto, forex, economy, indices

### 2. Add tool definition
```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def new_tool_name(
    param1: str,
    param2: Optional[int] = None,
) -> str:
    """Description of what this tool does."""
    try:
        results = client.sdk_method(
            param1=param1,
            param2=param2,
            raw=True,
        )
        return formatter(results.data.decode("utf-8"))
    except Exception as e:
        return f"Error: {e}"
```

### 3. That's it!
No changes needed to `server.py` - the tool is automatically registered.

## Rollback Instructions

If you need to restore the original monolithic file:

```bash
cp src/mcp_polygon/server_backup.py src/mcp_polygon/server.py
```

## Testing Checklist

### Before Deployment
- [ ] All syntax checks pass: `python3 -m py_compile src/mcp_polygon/server.py`
- [ ] All modules compile: `python3 -m py_compile src/mcp_polygon/tools/*.py`
- [ ] Import test: `python3 -c "from mcp_polygon import server"`
- [ ] Tool count: Verify 53 tools registered
- [ ] Existing tests: Run full test suite

### After Deployment
- [ ] All 53 tools accessible
- [ ] Tool responses unchanged
- [ ] Performance unchanged
- [ ] No import errors
- [ ] No runtime errors

## Module Structure

Each module follows this pattern:

```python
def register_tools(mcp, client, formatter):
    """
    Register all [asset-class]-related tools.

    Args:
        mcp: FastMCP instance
        client: Polygon RESTClient instance
        formatter: json_to_csv function
    """
    from mcp.types import ToolAnnotations

    @mcp.tool(...)
    async def tool_name(...):
        ...
```

## Key Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Main file size | 2,006 lines | 38 lines | -98% |
| Tools | 53 | 53 | 0% |
| Modules | 1 | 7 | +600% |
| Scalability | Low | High | ✅ |
| Maintainability | Low | High | ✅ |

## Phase 2 Readiness

The architecture supports adding ~40 indices tools without bloat:
- `indices.py` already created and registered
- Just add tool definitions
- No structural changes needed

## Important Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| server.py | Orchestrator | 38 | ✅ Active |
| server_backup.py | Rollback safety | 2,006 | 💾 Backup |
| tools/__init__.py | Module registry | 7 | ✅ Active |
| tools/stocks.py | Stock tools | 1,658 | ✅ Active |
| tools/futures.py | Futures tools | 437 | ✅ Active |
| tools/economy.py | Economy tools | 88 | ✅ Active |
| tools/forex.py | Forex tools | 60 | ✅ Active |
| tools/crypto.py | Crypto tools | 50 | ✅ Active |
| tools/options.py | Options tools | 37 | ✅ Active |
| tools/indices.py | Indices placeholder | 12 | 📝 Phase 2 |

## Common Issues & Solutions

### Import Error
**Issue**: `ModuleNotFoundError: No module named 'mcp_polygon.tools'`
**Solution**: Ensure `tools/__init__.py` exists and is not empty

### Tool Not Registered
**Issue**: Tool defined but not accessible
**Solution**: Check that module's `register_tools()` is called in `server.py`

### Syntax Error
**Issue**: Python syntax error in module
**Solution**: Run `python3 -m py_compile <module.py>` to identify line

### Missing Dependency
**Issue**: `ModuleNotFoundError: No module named 'polygon'`
**Solution**: Install dependencies: `pip install -e .`

## Quick Commands

### Verify Structure
```bash
ls -la src/mcp_polygon/tools/
```

### Count Tools
```bash
grep -c "@mcp.tool" src/mcp_polygon/tools/*.py | awk -F: '{s+=$2} END {print "Total:", s}'
```

### Check Syntax
```bash
python3 -m py_compile src/mcp_polygon/server.py
python3 -m py_compile src/mcp_polygon/tools/*.py
```

### View Module
```bash
cat src/mcp_polygon/tools/stocks.py
```

## Contact & Support

For issues or questions:
1. Check `/Users/chris/Projects/mcp_polygon/REFACTORING_COMPLETE.md`
2. Review syntax with `python3 -m py_compile`
3. Verify tool count matches 53
4. Test with existing test suite

---

**Status**: Production Ready
**Date**: October 15, 2025
**Version**: Modular Architecture v1.0
**Backward Compatible**: 100%
