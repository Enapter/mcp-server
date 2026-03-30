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
  enapter/mcp-server:v0.11.0
```

The server can be configured using environment variables and command-line
arguments.

## Available Tools

The server exposes the following tools for interacting with the Enapter EMS:

| Tool                        | Description                                                      |
| --------------------------- | ---------------------------------------------------------------- |
| `search_sites`              | Search among all sites with name and timezone regex filtering    |
| `search_devices`            | Search devices by site, type, and name regex filtering           |
| `search_command_executions` | Search the history of command executions                         |
| `read_blueprint`            | Access device blueprint sections (properties, telemetry, alerts) |
| `get_historical_telemetry`  | Retrieve time-series telemetry with configurable granularity     |

## Example Workflows

### 1. Diagnostic Troubleshooting

**Goal**: Investigate a specific device failure or alert.

- Identify the device using `search_devices(view="full")` to see `active_alerts`.
- Cross-reference alerts with `read_blueprint(section="alerts")` for their definitions.
- Use `search_command_executions` to audit actions recently taken.

### 2. Historical Analysis & Performance Yield

**Goal**: Analyze performance trends (e.g., hydrogen yield, energy storage).

- Find the correct metric name via `read_blueprint(section="telemetry")`.
- Fetch the data with `get_historical_telemetry`.

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
