# Copilot Instructions for Enapter MCP Server

## Project Overview

This is a Model Context Protocol (MCP) server that provides integration with the Enapter EMS (Energy Management System). The server exposes tools for AI assistants and MCP clients to interact with Enapter sites, devices, and telemetry data.

## Technology Stack

- **Language**: Python 3.14+
- **Framework**: FastMCP (v2.14.*)
- **API Client**: Enapter Python SDK (v0.14.4)
- **Package Manager**: pipenv
- **Containerization**: Docker

## Development Setup

### Prerequisites
- Python 3.14 or higher
- pipenv for dependency management
- Docker (for containerized deployment)

### Installation
```bash
make install-deps  # Install dependencies using pipenv
```

### Running Tests
```bash
make test  # Run integration tests
```

### Running Checks
```bash
make check  # Run all linting and tests
```

## Code Style and Quality

This project enforces strict code quality standards using multiple linters:

### Code Formatting
- **black**: Python code formatter (enforced in CI)
- **isort**: Import statement organizer (enforced in CI)

### Code Quality
- **pyflakes**: Code checker for Python
- **mypy**: Static type checker (all code must be type-annotated)

### Running Linters
```bash
make lint          # Run all linters
make lint-black    # Check black formatting
make lint-isort    # Check import sorting
make lint-pyflakes # Check code quality
make lint-mypy     # Check type annotations
```

## Project Structure

```
src/enapter_mcp_server/
├── __init__.py          # Version and package info
├── __main__.py          # Entry point
├── cli/                 # Command-line interface
├── mcp/                 # MCP server implementation
│   ├── server.py        # Main MCP server with tools
│   ├── client.py        # Enapter API client wrapper
│   └── models/          # Data models
└── py.typed             # PEP 561 marker file
```

## Key Components

### MCP Tools
The server exposes the following tools (defined in `src/enapter_mcp_server/mcp/server.py`):
- `search_sites`: Search sites with regex filtering and pagination
- `get_site_context`: Get detailed site information with device statistics
- `search_devices`: Filter devices by site, type, and name pattern
- `get_device_context`: Get comprehensive device data
- `read_blueprint`: Access device blueprint sections
- `get_historical_telemetry`: Retrieve time-series telemetry data

### Authentication
All tool invocations require authentication via the `X-Enapter-Auth-Token` HTTP header.

### Environment Variables
- `ENAPTER_MCP_SERVER_ADDRESS`: Server listening address (default: `127.0.0.1:8000`)
- `ENAPTER_HTTP_API_URL`: Enapter HTTP API base URL (default: `https://api.enapter.com`)

## Testing

- Tests are located in the `tests/` directory
- Integration tests are in `tests/integration/`
- Use pytest with asyncio support (configured in `pytest.ini`)
- Run tests with: `make test-integration` or `make test`

## Continuous Integration

The CI pipeline (`.github/workflows/ci.yml`) runs on every push:
1. Sets up Python 3.14
2. Installs dependencies with pipenv
3. Runs all checks (linting and testing)
4. Builds Docker image
5. Pushes to Docker Hub on version tags

## Docker

### Building
```bash
make docker-image  # Build with default tag
DOCKER_IMAGE_TAG=custom:tag make docker-image  # Custom tag
```

### Running
```bash
docker run --rm -p 8000:8000 enapter/mcp-server:v0.5.0 serve
```

## Contributing Guidelines

When making changes to this repository:

1. **Follow the existing code style**: All code must pass black, isort, pyflakes, and mypy checks
2. **Add type annotations**: All functions and methods must have type hints
3. **Write tests**: Add integration tests for new features in `tests/integration/`
4. **Update documentation**: Keep README.md and docstrings up to date
5. **Use semantic versioning**: Version is defined in `src/enapter_mcp_server/__init__.py`
6. **Test Docker builds**: Ensure `make docker-image` succeeds before committing

## Common Tasks

### Updating Dependencies
```bash
make update-deps
```

### Bumping Version
```bash
make bump-version V=0.6.0
```

### Building and Testing Locally
```bash
make install-deps
make check
make docker-image
```

## Additional Notes

- The project uses a `py.typed` marker file for PEP 561 compliance
- All Python files should be in the `src/enapter_mcp_server` package
- Configuration files include `.isort.cfg` for import sorting preferences
- The server uses FastMCP framework for MCP protocol implementation
