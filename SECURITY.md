# Security Policy

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, please report security issues by opening a private security advisory at:
https://github.com/ChrisSc/mcp_polygon/security/advisories/new

Or email security concerns to: clscragg@protonmail.com

### What to Include

When reporting a security issue, please include:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.5.x   | :x:                |
| < 0.5   | :x:                |

## Security Update Process

- **Critical vulnerabilities**: Hotfix release within 48 hours
- **High severity**: Patch release within 7 days
- **Medium/Low severity**: Included in next scheduled release

## Responsible Disclosure

We follow a 90-day disclosure timeline:
1. Issue reported privately
2. Fix developed and tested
3. Security patch released
4. Public disclosure after patch is available
5. Credit given to reporter (unless anonymity requested)

## Security Best Practices for Users

### API Key Management

- **Never commit** your `POLYGON_API_KEY` to version control
- Use environment variables for API key storage
- Rotate API keys quarterly
- Use read-only API keys if Polygon.io supports scoped permissions

### Installation Security

When installing this MCP server:

1. **Verify the source**:
   ```bash
   # Always install from specific version tags
   uvx --from git+https://github.com/ChrisSc/mcp_polygon@v1.0.0 mcp_polygon
   ```

2. **Review changes** before upgrading:
   ```bash
   # Check what changed between versions
   git diff v1.0.0..v1.1.0
   ```

3. **Monitor API usage** for anomalies at polygon.io dashboard

### Running Locally

- Keep dependencies updated (`uv sync`)
- Run in isolated environments (virtual env, Docker)
- Use `.env` files for local development (never commit them)

## Known Security Considerations

### Current Architecture

This MCP server is a **stateless proxy**:
- ✅ No data storage or caching
- ✅ No authentication logic (delegated to Polygon.io)
- ✅ Read-only operations only
- ✅ No user data collection
- ✅ All API calls go through official Polygon.io SDK

### Dependencies

We use:
- `mcp[cli]` - Official MCP Python SDK (modelcontextprotocol.io)
- `polygon-api-client` - Official Polygon.io Python SDK

All dependencies are pinned in `uv.lock` with SHA256 hashes.

## Security Audit History

| Date       | Version | Rating | Summary |
|------------|---------|--------|---------|
| 2025-10-15 | 1.0.0   | 8/10   | Production-ready, no critical issues |
| 2025-01-XX | 0.5.0   | 8/10   | Initial production release |

## Contact

For security-related questions or concerns:
- **GitHub Security Advisories**: https://github.com/ChrisSc/mcp_polygon/security/advisories
- **Fork Maintainer**: Chris Scragg (@ChrisSc) - clscragg@protonmail.com
- **Upstream Security**: For Polygon.io API security, contact support@polygon.io
