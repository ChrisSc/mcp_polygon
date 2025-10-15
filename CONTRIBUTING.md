# Contributing to mcp_polygon (Fork)

This is a maintained fork of the official [Polygon.io MCP Server](https://github.com/polygon-io/mcp_polygon). Contributions are welcome!

## Quick Start

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Run linting (`just lint`)
6. Commit your changes (`git commit -m 'Add feature'`)
7. Push to your fork (`git push origin feature/my-feature`)
8. Open a Pull Request

## Development Setup

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

```bash
# Clone the repository
git clone https://github.com/ChrisSc/mcp_polygon.git
cd mcp_polygon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
uv sync

# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v
```

## What to Contribute

### Fork-Specific Improvements
- Documentation enhancements
- Bug fixes specific to this fork
- New tools/endpoints
- Performance optimizations
- Test coverage improvements

### Upstream-Worthy Contributions
If your contribution benefits the original Polygon.io MCP server, consider:
1. Opening an issue at [polygon-io/mcp_polygon](https://github.com/polygon-io/mcp_polygon/issues)
2. Submitting a PR there first
3. Backporting to this fork after upstream acceptance

## Code Style

This project uses:
- **Ruff** for linting and formatting
- **Pytest** for testing
- **Type hints** throughout the codebase

Run before committing:
```bash
just lint  # Runs ruff format + ruff check --fix
```

## Testing

All new features must include tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_formatters.py -v

# Run with coverage
pytest tests/ --cov=src/mcp_polygon --cov-report=html
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Documentation

Update relevant documentation:
- **README.md**: For user-facing changes
- **CLAUDE.md**: For development workflow changes
- **CHANGELOG.md**: Add entry for your change
- Docstrings: For new tools or functions

## Pull Request Process

1. **Open an Issue First** (for major changes)
   - Discuss your proposed changes
   - Get feedback before investing time

2. **PR Requirements**
   - Clear description of changes
   - Tests included
   - Documentation updated
   - Linting passing (`just lint`)
   - All tests passing (`pytest tests/ -v`)

3. **Response Time**
   - Best effort, typically 1-2 weeks for review
   - Smaller PRs are reviewed faster

## Getting Help

- **Fork Issues**: [ChrisSc/mcp_polygon/issues](https://github.com/ChrisSc/mcp_polygon/issues)
- **API Questions**: support@polygon.io or [Polygon.io Docs](https://polygon.io/docs)
- **MCP Questions**: [Model Context Protocol Docs](https://modelcontextprotocol.io)

## Code of Conduct

Be respectful, constructive, and professional. This is a community project.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
