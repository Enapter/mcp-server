# Enapter MCP Server

[![CI](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/v/enapter/mcp-server?label=Docker%20Hub)](https://hub.docker.com/r/enapter/mcp-server)

A Model Context Protocol (MCP) server that provides seamless integration with the [Enapter](https://www.enapter.com/) IoT platform. This server enables AI assistants and other MCP clients to interact with Enapter devices, sites, and telemetry data.

## Overview

The Enapter MCP Server exposes Enapter's HTTP API capabilities through the Model Context Protocol, allowing AI assistants to:

- List and retrieve information about sites
- Query device information with optional expanded data
- Fetch real-time telemetry data from multiple devices
- Monitor device connectivity and properties

## Features

- **Site Management**: List all accessible sites and retrieve detailed site information
- **Device Operations**: List and query devices with configurable data expansion
- **Telemetry Access**: Retrieve latest telemetry data from multiple devices simultaneously
- **Authentication**: Secure token-based authentication via HTTP headers
- **Async Architecture**: Built on modern Python async/await patterns
- **Docker Support**: Ready-to-use Docker images available

## Installation

### From PyPI (Coming Soon)

```bash
pip install enapter-mcp-server
```

### From Source

```bash
git clone https://github.com/Enapter/mcp-server.git
cd mcp-server
pipenv install
```

### Using Docker

```bash
docker pull enapter/mcp-server:latest
```

## Usage

### Running the Server

Start the MCP server with default settings:

```bash
python -m enapter_mcp_server serve
```

Or with custom configuration:

```bash
python -m enapter_mcp_server serve \
  --address 0.0.0.0:8080 \
  --enapter-http-api-url https://api.enapter.com
```

### Using Docker

```bash
docker run -p 8000:8000 enapter/mcp-server:latest serve
```

### Checking Server Status

Verify the server is running:

```bash
python -m enapter_mcp_server ping --address 127.0.0.1:8000
```

## Configuration

### Environment Variables

- `ENAPTER_MCP_SERVER_ADDRESS`: Server listening address (default: `127.0.0.1:8000`)
- `ENAPTER_HTTP_API_URL`: Enapter HTTP API base URL (default: `https://api.enapter.com`)

### Command-Line Options

```
usage: enapter_mcp_server [-h] [-a ADDRESS] {ping,serve} ...

options:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        Server address (default: 127.0.0.1:8000)

commands:
  {ping,serve}
    ping                Check if server is running
    serve               Start the MCP server
```

## Available MCP Tools

The server provides the following MCP tools:

### `list_sites`
List all sites to which the authenticated user has access.

**Returns**: Array of site objects

### `get_site`
Get detailed information about a specific site.

**Parameters**:
- `site_id` (string): The unique identifier of the site

**Returns**: Site object with detailed information

### `list_devices`
List devices with optional data expansion.

**Parameters**:
- `expand_manifest` (boolean, optional): Include device manifest data
- `expand_properties` (boolean, optional): Include device properties
- `expand_connectivity` (boolean, optional): Include connectivity information
- `site_id` (string, optional): Filter devices by site ID

**Returns**: Array of device objects

### `get_device`
Get detailed information about a specific device.

**Parameters**:
- `device_id` (string): The unique identifier of the device
- `expand_manifest` (boolean, optional): Include device manifest data
- `expand_properties` (boolean, optional): Include device properties
- `expand_connectivity` (boolean, optional): Include connectivity information

**Returns**: Device object with detailed information

### `get_latest_telemetry`
Retrieve the latest telemetry data from multiple devices.

**Parameters**:
- `attributes_by_device` (object): Map of device IDs to arrays of attribute names

**Returns**: Map of device IDs to telemetry data

**Example**:
```json
{
  "device-123": ["temperature", "pressure"],
  "device-456": ["voltage", "current"]
}
```

## Authentication

The server requires authentication via the `x-enapter-auth-token` HTTP header. This token is provided by MCP clients when making requests to the server.

To obtain an API token, visit your [Enapter account settings](https://cloud.enapter.com/).

## Development

### Prerequisites

- Python 3.11 or higher
- pipenv
- Docker (optional, for containerized development)

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/Enapter/mcp-server.git
cd mcp-server
```

2. Install dependencies:
```bash
make install-deps
```

### Running Tests

Run the full test suite:

```bash
make test
```

Run with verbose output:

```bash
make test-integration
```

### Code Quality

Run all linting checks:

```bash
make lint
```

Individual linters:

```bash
make lint-black    # Code formatting
make lint-isort    # Import sorting
make lint-pyflakes # Static analysis
make lint-mypy     # Type checking
```

### Building

Run all checks (lint + test):

```bash
make check
```

Build Docker image:

```bash
make docker-image
```

Or with a custom tag:

```bash
make docker-image DOCKER_IMAGE_TAG=my-custom-tag
```

## Project Structure

```
mcp-server/
├── src/
│   └── enapter_mcp_server/
│       ├── cli/           # Command-line interface
│       ├── mcp/           # MCP server and client implementation
│       ├── __init__.py    # Package version
│       └── __main__.py    # Entry point
├── tests/
│   └── integration/       # Integration tests
├── Dockerfile             # Docker image definition
├── Makefile               # Development commands
├── Pipfile                # Python dependencies
└── setup.py               # Package configuration
```

## Dependencies

- [enapter](https://pypi.org/project/enapter/) - Enapter Python SDK
- [fastmcp](https://pypi.org/project/fastmcp/) - Fast MCP server implementation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Versioning

To bump the version:

```bash
make bump-version V=0.2.0
```

## License

See the [LICENSE](LICENSE) file for details.

## Links

- [Enapter Website](https://www.enapter.com/)
- [Enapter Cloud](https://cloud.enapter.com/)
- [Enapter API Documentation](https://developers.enapter.com/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## Support

For issues, questions, or contributions, please use the [GitHub Issues](https://github.com/Enapter/mcp-server/issues) page.

---

Made with ❤️ by [Enapter](https://www.enapter.com/)
