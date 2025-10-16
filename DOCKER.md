# Docker HTTP Transport Setup Guide

This guide explains how to run the MCP Polygon server in Docker with HTTP transport and connect Claude Desktop to it.

## Quick Start

```bash
# 1. Ensure .env file exists with your API key
cp .env.example .env
# Edit .env and add your POLYGON_API_KEY

# 2. Start the Docker server
docker-compose up -d

# 3. Verify server is running
docker logs mcp_polygon_server

# 4. Test the endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

## Server Details

**Endpoint**: `http://localhost:8000/mcp`

**Configuration**:
- Transport: `streamable-http` (Server-Sent Events)
- Protocol: MCP v2024-11-05
- Tools: 81 tools across 7 asset classes
- Binding: `0.0.0.0:8000` (container) → `127.0.0.1:8000` (host)

**Security**:
- ✅ DNS rebinding protection enabled
- ✅ Localhost-only binding on host
- ✅ Read-only filesystem
- ✅ Dropped Linux capabilities
- ✅ No new privileges

## Claude Desktop Configuration

### Option 1: Using the Provided Config File

1. Copy the configuration from [`claude_desktop_config_http.json`](./claude_desktop_config_http.json)

2. Locate your Claude Desktop config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. Add the `mcpServers` section:
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

4. Restart Claude Desktop

### Option 2: Manual Configuration

Edit your `claude_desktop_config.json`:

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

**Important**:
- No `command`, `args`, or `env` fields needed for HTTP transport
- The Docker server must be running before starting Claude Desktop
- API key is configured in Docker via `.env` file

## Server Management

```bash
# Start server (detached mode)
docker-compose up -d

# View logs
docker logs mcp_polygon_server

# Follow logs
docker logs -f mcp_polygon_server

# Stop server
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# Check server status
docker ps | grep mcp_polygon_server

# Check if endpoint is accessible
curl -I http://localhost:8000/mcp
```

## Verification

### 1. Check Server Status

```bash
docker logs mcp_polygon_server
```

Expected output:
```
Starting Polygon MCP server with API key configured.
Starting MCP server with transport: streamable-http
HTTP server will listen on: http://0.0.0.0:8000/mcp
INFO:     Started server process [10]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Test MCP Protocol

```python
import httpx
import json
import re

# Initialize session
headers = {
    'Accept': 'application/json, text/event-stream',
    'Content-Type': 'application/json'
}

init_payload = {
    'jsonrpc': '2.0',
    'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'test', 'version': '1.0'}
    },
    'id': 1
}

response = httpx.post(
    'http://localhost:8000/mcp',
    json=init_payload,
    headers=headers,
    timeout=5.0
)

print(f"Status: {response.status_code}")
print(f"Session ID: {response.headers.get('mcp-session-id')}")

# Parse SSE response
match = re.search(r'data: (.+)', response.text)
if match:
    data = json.loads(match.group(1))
    print(f"Server: {data['result']['serverInfo']['name']}")
    print(f"Version: {data['result']['serverInfo']['version']}")
```

### 3. List Available Tools

```python
# Get session ID from initialize response
session_id = response.headers['mcp-session-id']
headers['mcp-session-id'] = session_id

# Send initialized notification
httpx.post(
    'http://localhost:8000/mcp',
    json={'jsonrpc': '2.0', 'method': 'notifications/initialized'},
    headers=headers,
    timeout=5.0
)

# List tools
tools_payload = {
    'jsonrpc': '2.0',
    'method': 'tools/list',
    'id': 2
}

response = httpx.post(
    'http://localhost:8000/mcp',
    json=tools_payload,
    headers=headers,
    timeout=5.0
)

match = re.search(r'data: (.+)', response.text)
data = json.loads(match.group(1))
tools = data['result']['tools']
print(f"Available tools: {len(tools)}")
for tool in tools[:10]:
    print(f"  - {tool['name']}")
```

### 4. Call a Tool

```python
# Call get_previous_close_agg for AAPL
tool_call = {
    'jsonrpc': '2.0',
    'method': 'tools/call',
    'params': {
        'name': 'get_previous_close_agg',
        'arguments': {'ticker': 'AAPL'}
    },
    'id': 3
}

response = httpx.post(
    'http://localhost:8000/mcp',
    json=tool_call,
    headers=headers,
    timeout=10.0
)

match = re.search(r'data: (.+)', response.text)
data = json.loads(match.group(1))
content = data['result']['content'][0]['text']
print(f"Result:\n{content}")
```

Expected output:
```
T,v,vw,o,c,h,l,t,n
AAPL,33888905.0,249.5813,249.485,249.34,251.82,247.47,1760558400000,528778
```

## Troubleshooting

### Server Won't Start

**Error**: "Read-only file system"

**Solution**: This was fixed by adding `/root/.cache` to tmpfs mounts in `docker-compose.yml`. Ensure you have the latest version:

```yaml
tmpfs:
  - /tmp
  - /root/.cache  # Required for uv package manager
```

### Connection Refused

**Issue**: Can't connect to `http://localhost:8000/mcp`

**Checks**:
1. Is the Docker server running? `docker ps | grep mcp_polygon_server`
2. Is port 8000 available? `lsof -i :8000`
3. Check Docker logs: `docker logs mcp_polygon_server`

### Empty Reply from Server

**Issue**: curl returns "Empty reply from server"

**Solution**: The streamable-http transport requires proper headers:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Tools Not Available

**Issue**: Server returns 0 tools

**Solution**: Send the `notifications/initialized` message after initialize:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### API Key Not Working

**Issue**: "Invalid API key" or "Not authorized" errors

**Checks**:
1. Is `.env` file present? `ls -la .env`
2. Is `POLYGON_API_KEY` set in `.env`? `cat .env | grep POLYGON_API_KEY`
3. Is the container picking up the env var? `docker exec mcp_polygon_server env | grep POLYGON_API_KEY`

## Advantages of HTTP Transport

**✅ Independent Server**
- Server runs independently of Claude Desktop
- Can restart Claude Desktop without restarting the server
- Server persists across Claude Desktop sessions

**✅ Multi-Client Support**
- Multiple MCP clients can connect to the same server
- Useful for testing with MCP Inspector while using Claude Desktop

**✅ Better Debugging**
- Easy to view logs: `docker logs -f mcp_polygon_server`
- Can test with curl or Python scripts
- Clear separation between server and client issues

**✅ Resource Isolation**
- Server runs in isolated Docker container
- Container security hardening (read-only, dropped capabilities)
- Predictable resource usage

## Disadvantages of HTTP Transport

**❌ Additional Complexity**
- Requires Docker to be running
- Extra step to start/stop the server
- More configuration than stdio transport

**❌ Network Overhead**
- Small latency increase (~10-50ms) vs stdio
- Not noticeable for interactive use
- May impact batch operations

**❌ Port Management**
- Port 8000 must be available
- Potential conflicts with other services
- Localhost binding limits remote access

## When to Use HTTP vs STDIO

### Use HTTP Transport When:
- You want server to run independently of Claude Desktop
- You need to connect multiple clients to the same server
- You want better debugging and logging capabilities
- You prefer Docker-based deployments

### Use STDIO Transport When:
- You want the simplest setup (default)
- You prefer Claude Desktop to manage the server lifecycle
- You don't need multi-client support
- You want minimal latency

## Security Notes

The Docker HTTP transport is configured for **local development only**:

1. **Localhost Binding**: Port mapping `127.0.0.1:8000:8000` prevents network exposure
2. **DNS Rebinding Protection**: Origin validation per MCP specification
3. **Container Hardening**: Read-only filesystem, dropped capabilities, no new privileges
4. **API Key Security**: Stored in `.env` file (not in Claude Desktop config)

**Security Level**: 8/10 (Production-ready for local development)

For production deployments, additional considerations:
- Use TLS/HTTPS with proper certificates
- Implement additional authentication (API tokens, OAuth)
- Use secrets management (Docker secrets, vault)
- Configure firewall rules
- Monitor API usage and rate limits

## References

- [MCP Specification](https://modelcontextprotocol.io)
- [MCP Streamable HTTP Transport](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Polygon.io API Documentation](https://polygon.io/docs)

## Support

For issues related to:
- **Docker setup**: Check [DOCKER.md](./DOCKER.md) troubleshooting section
- **MCP configuration**: See [README.md](./README.md) Claude Desktop section
- **Server implementation**: See [CLAUDE.md](./CLAUDE.md) development guide
- **Polygon API**: Contact support@polygon.io

**Fork Repository**: https://github.com/ChrisSc/mcp_polygon
**Maintainer**: Chris Scragg (@ChrisSc)
