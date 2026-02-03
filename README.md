# Enapter MCP Server

[![CI](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/v/enapter/mcp-server?label=Docker%20Hub)](https://hub.docker.com/r/enapter/mcp-server)

## Overview

A Model Context Protocol (MCP) server that provides seamless integration with
the [Enapter EMS](https://www.enapter.com/). This server enables AI assistants
and other MCP clients to interact with Enapter sites, devices and telemetry
data.

## Features

The server exposes 6 MCP tools for interacting with Enapter EMS:

- **`search_sites`**: Search sites with regex filtering (name, timezone) and pagination
- **`get_site_context`**: Get detailed site information with device statistics
- **`search_devices`**: Filter devices by site, type, and name pattern
- **`get_device_context`**: Get comprehensive device data (connectivity, properties, telemetry)
- **`read_blueprint`**: Access device blueprint sections (properties, telemetry, alerts)
- **`get_historical_telemetry`**: Retrieve time-series telemetry with configurable granularity

Additional features:

- **Authentication**: Secure token-based authentication via HTTP headers
- **Async Architecture**: Built on modern Python async/await patterns
- **Docker Support**: Ready-to-use Docker images available
- **CLI Tools**: Multiple commands for server management and testing

## Installation

Pull the latest image from Docker Hub:

```bash
docker pull enapter/mcp-server:v0.5.0
```

## Usage

### Starting the Server

```bash
docker run --rm --name enapter-mcp-server \
  -p 8000:8000 \
  enapter/mcp-server:v0.5.0 serve
```

> [!NOTE]
> The server itself doesn't require `ENAPTER_HTTP_API_TOKEN` to start. 
> The token is provided by MCP clients when they make requests to the server via the `X-Enapter-Auth-Token` HTTP header.

### Available CLI Commands

The server provides several CLI commands:

- **`serve`**: Start the MCP server (default address: `127.0.0.1:8000`)
- **`ping`**: Check if the server is running and responsive
- **`list_tools`**: List all available MCP tools with their schemas
- **`call_tool`**: Invoke a specific tool with JSON arguments (requires `ENAPTER_HTTP_API_TOKEN`)
- **`version`**: Display the server version

#### Examples

Check server health:

```bash
docker exec -it enapter-mcp-server python -m enapter_mcp_server ping
```

List available tools:

```bash
docker exec -it enapter-mcp-server python -m enapter_mcp_server list_tools
```

Call a tool (requires authentication):

```bash
docker exec -it enapter-mcp-server \
  env ENAPTER_HTTP_API_TOKEN=your_api_token_here \
  python -m enapter_mcp_server call_tool search_sites \
  --arguments '{"name_pattern": ".*", "limit": 5}'
```

Display version:

```bash
docker exec -it enapter-mcp-server python -m enapter_mcp_server version
```

### Configuration

#### Environment Variables

- **`ENAPTER_MCP_SERVER_ADDRESS`**: Server listening address (default: `127.0.0.1:8000`)
- **`ENAPTER_HTTP_API_URL`**: Enapter HTTP API base URL (default: `https://api.enapter.com`)
- **`ENAPTER_HTTP_API_TOKEN`**: Your Enapter API token (required only for the `call_tool` CLI command)

#### CLI Flags

- **`-a, --address`**: Override the server address
- **`-u, --enapter-http-api-url`**: Override the Enapter API URL

Example with custom configuration:

```bash
docker run --rm --name enapter-mcp-server \
  -p 9000:9000 \
  enapter/mcp-server:v0.5.0 \
  --address 0.0.0.0:9000 \
  --enapter-http-api-url https://custom-api.example.com \
  serve
```

## Authentication

The server requires authentication via the `X-Enapter-Auth-Token` HTTP header for all tool invocations.
MCP clients must provide this token when making requests to the server.

When using the `call_tool` CLI command, provide your token via the `ENAPTER_HTTP_API_TOKEN` 
environment variable as shown in the examples above.

To obtain an API token, see the [API
reference](https://v3.developers.enapter.com/reference/http/intro#api-token).

## Development

### Running Tests

```bash
make test
```

### Running Linters

```bash
make lint
```

### Running All Checks

```bash
make check  # Runs both lint and test
```

### Building Docker Image

```bash
make docker-image
```

## Support

For issues, questions, or contributions, please use the [GitHub
Issues](https://github.com/Enapter/mcp-server/issues) page.

---

Made with ❤️ by [Enapter](https://www.enapter.com/)
