# Enapter MCP Server

[![CI](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Enapter/mcp-server/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/v/enapter/mcp-server?label=Docker%20Hub)](https://hub.docker.com/r/enapter/mcp-server)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A Model Context Protocol (MCP) server that provides seamless integration with
the [Enapter EMS](https://enapter.com/en/enapter-products-aem/ems-toolkit/).
This server enables AI assistants and other MCP clients to interact with
Enapter sites, devices and telemetry data.

## Connecting Your AI Application

The Enapter MCP Server is available as a public hosted service at
`https://mcp.enapter.com/mcp`. It uses streamable HTTP transport and OAuth 2.0
for authentication.

For specific instructions on how to connect your preferred AI client, please
refer to the following guides:

- [Claude Desktop](https://v3.developers.enapter.com/docs/claude-desktop-mcp/)
- [Claude Mobile](https://v3.developers.enapter.com/docs/claude-mobile-mcp/)
- [Claude Code](https://v3.developers.enapter.com/docs/claude-code-mcp/)
- [Copilot Studio](https://v3.developers.enapter.com/docs/copilot-studio-mcp/)
- [ChatGPT](https://v3.developers.enapter.com/docs/chatgpt-mcp/)

## Self-Hosting

If you prefer to run your own instance, you can self-host the server using
Docker:

```bash
docker run --rm --name enapter-mcp-server \
  -p 8000:8000 \
  enapter/mcp-server:v0.10.0
```

The server can be configured using environment variables and command-line
arguments.

## Available Tools

The server exposes the following tools for interacting with the Enapter EMS:

| Tool                       | Description                                                             |
| -------------------------- | ----------------------------------------------------------------------- |
| `search_sites`             | Search sites with regex filtering (name, timezone) and pagination       |
| `get_site_details`         | Get detailed site information with device and active alert statistics   |
| `search_devices`           | Filter devices by site, type, and name pattern                          |
| `get_device_details`       | Get comprehensive device data (connectivity, properties, active alerts) |
| `read_blueprint_manifest`  | Access device blueprint sections (properties, telemetry, alerts)        |
| `get_historical_telemetry` | Retrieve time-series telemetry with configurable granularity            |

## Support

For issues, questions, or contributions, please:

- Email us at [support@enapter.com](mailto:support@enapter.com).
- Open a [GitHub Issue](https://github.com/Enapter/mcp-server/issues).
- Join our [Discord server](https://discord.com/invite/TCaEZs3qpe).
- Check our [Contributing Guide](CONTRIBUTING.md).

## Privacy Policy

For information about how we handle data, please refer to the [Enapter Privacy
Policy](https://www.enapter.com/privacy-policy).

---

Made with ❤️ by [Enapter](https://www.enapter.com/)
