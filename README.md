# Enapter MCP Server

[![CI](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/v/enapter/mcp-server?label=Docker%20Hub)](https://hub.docker.com/r/enapter/mcp-server)

## Overview

A Model Context Protocol (MCP) server that provides seamless integration with
the [Enapter EMS](https://www.enapter.com/). This server enables AI assistants
and other MCP clients to interact with Enapter sites, devices and telemetry
data.

## Features

- **Site Management**: List all accessible sites and retrieve detailed site information
- **Device Operations**: List and query devices with configurable data expansion
- **Telemetry Access**: Retrieve latest telemetry data from multiple devices simultaneously
- **Authentication**: Secure token-based authentication via HTTP headers
- **Async Architecture**: Built on modern Python async/await patterns
- **Docker Support**: Ready-to-use Docker images available

## Installation

### Install Using Docker

```bash
docker pull enapter/mcp-server:v0.3.2
```

## Usage

### Run Using Docker

```bash
docker run --name enapter-mcp-server -p 8000:8000 enapter/mcp-server:v0.3.2 serve
```

### Check Server Status

Verify the server is running:

```bash
docker exec -it enapter-mcp-server python -m enapter_mcp_server ping
```

### Configure Environment Variables

- `ENAPTER_MCP_SERVER_ADDRESS`: Server listening address (default: `127.0.0.1:8000`)
- `ENAPTER_HTTP_API_URL`: Enapter HTTP API base URL (default: `https://api.enapter.com`)

## Authentication

The server requires authentication via the `X-Enapter-Auth-Token` HTTP header.
This token is provided by MCP clients when making requests to the server.

To obtain an API token, see [API
reference](https://v3.developers.enapter.com/reference/http/intro#api-token).

## Support

For issues, questions, or contributions, please use the [GitHub
Issues](https://github.com/Enapter/mcp-server/issues) page.

---

Made with ❤️ by [Enapter](https://www.enapter.com/)
