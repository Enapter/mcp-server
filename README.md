# Enapter MCP Server

[![CI](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/v/enapter/mcp-server?label=Docker%20Hub)](https://hub.docker.com/r/enapter/mcp-server)

## Overview

A Model Context Protocol (MCP) server that provides seamless integration with
the [Enapter EMS](https://www.enapter.com/). This server enables AI assistants
and other MCP clients to interact with Enapter sites, devices and telemetry
data.

## Tools

The server exposes the following tools for interacting with Enapter EMS:

- **`search_sites`**: Search sites with regex filtering (name, timezone) and pagination
- **`get_site_context`**: Get detailed site information with device statistics
- **`search_devices`**: Filter devices by site, type, and name pattern
- **`get_device_context`**: Get comprehensive device data (connectivity, properties, telemetry)
- **`read_blueprint`**: Access device blueprint sections (properties, telemetry, alerts)
- **`get_historical_telemetry`**: Retrieve time-series telemetry with configurable granularity

## Usage

### Run Using Docker

```bash
docker run --rm --name enapter-mcp-server \
  -p 8000:8000 \
  enapter/mcp-server:v0.8.2 serve
```

### Configure Env Variables

- **`ENAPTER_MCP_SERVER_ADDRESS`**: Server listening address (default: `127.0.0.1:8000`)
- **`ENAPTER_HTTP_API_URL`**: Enapter HTTP API base URL (default: `https://api.enapter.com`)

## Authentication

The server requires authentication via the `X-Enapter-Auth-Token` HTTP header for all tool invocations.
MCP clients must provide this token when making requests to the server.

To obtain an API token, see the [API
reference](https://v3.developers.enapter.com/reference/http/intro#api-token).

## Support

For issues, questions, or contributions, please use the [GitHub
Issues](https://github.com/Enapter/mcp-server/issues) page.

---

Made with ❤️ by [Enapter](https://www.enapter.com/)
