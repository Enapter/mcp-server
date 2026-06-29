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
  enapter/mcp-server:v1.8.0
```

The server can be configured using environment variables and command-line
arguments.

## Available Tools

The server exposes the following tools for interacting with the Enapter EMS:

| Tool                        | Description                                                      | Access     | Default  |
| --------------------------- | ---------------------------------------------------------------- | ---------- | -------- |
| `search_sites`              | Search among all sites with name and timezone regex filtering    | Read-only  | Enabled  |
| `search_devices`            | Search devices by site, type, and name regex filtering           | Read-only  | Enabled  |
| `search_command_executions` | Search the history of command executions                         | Read-only  | Enabled  |
| `read_blueprint`            | Access device blueprint sections (properties, telemetry, alerts) | Read-only  | Enabled  |
| `get_historical_telemetry`  | Retrieve time-series telemetry with configurable granularity     | Read-only  | Enabled  |
| `search_rules`              | Search for automation rules within a specific site               | Read-only  | Enabled  |
| `read_rule`                 | Read the paginated lines of a rule's Lua script                  | Read-only  | Enabled  |
| `execute_command`           | Execute a command on a device                                    | Read-write | Disabled |
| `create_rule`               | Create a disabled MCP-managed automation rule                    | Read-write | Disabled |
| `edit_rule`                 | Apply a content-match edit to a disabled MCP-managed rule        | Read-write | Disabled |
| `delete_rule`               | Delete a disabled MCP-managed automation rule                    | Read-write | Disabled |

## Usage Examples

Here are realistic examples of how you can interact with your Enapter devices using AI assistants:

### Example 1: Diagnostic Troubleshooting

**User prompt:**

> One of our inverters just went offline. Can you check its status and tell me
> what the active alerts mean?

**What happens:**

- Server finds the specific inverter device
- Retrieves its current connectivity status and active alerts
- Reads the device blueprint to translate alert codes into human-readable descriptions
- Presents a summary of the issue to the user

### Example 2: Historical Analysis & Performance

**User prompt:**

> What was the average power consumption and temperature for the main HVAC
> system over the last 7 days?

**What happens:**

- Server locates the HVAC system device
- Checks its blueprint to identify the correct telemetry metric names for power consumption and temperature
- Fetches the historical telemetry data for the requested time period
- Calculates and presents the averages to the user

### Example 3: Auditing Command Executions

**User prompt:**

> Check if anyone tried to turn on the water pump this morning. Were there any
> errors during the execution?

**What happens:**

- Server locates the specific water pump device
- Reads the device blueprint to find the exact command name for "turning on" the device
- Searches the command execution history for that specific command executed this morning
- Retrieves the execution status and any associated error messages
- Reports back whether the command succeeded or failed

### Example 4: Auditing Automation Rules

**User prompt:**

> Can you check the automation rules running at the Alpha site? I need to verify
> the logic that automatically starts the electrolyser when excess solar power
> is available.

**What happens:**

- Server searches for rules within the specified site using `search_rules`
- Identifies the relevant rule based on its name/slug
- Retrieves the rule's Lua script using `read_rule`
- Analyzes the logic and confirms the exact threshold and conditions that trigger the electrolyser

### Example 5: Executing a Command (Human Confirmation Required)

> ⚠️ `execute_command` is **destructive** — it acts on real physical hardware
> (pumps, electrolysers, valves, inverters). It is **disabled by default**. Enable
> it with `--command-execution-enabled` on the command line or by setting
> `ENAPTER_COMMAND_EXECUTION_ENABLED=1`.

**User prompt:**

> The electrolyser at the Alpha site has been running for a long time. Please
> reboot it for me.

**What happens:**

- Server locates the electrolyser device using `search_devices`
- Reads the device blueprint with `read_blueprint(section="commands")` to
  discover the `reboot` command and checks whether it declares a `confirmation`
  block
- The `reboot` command declares a `confirmation` with a `title` and
  `description` (e.g. _"Reboot the electrolyser"_ / _"This will restart the
  device and interrupt production."_), so the assistant **presents these to the
  human and waits for explicit approval** — it does not act on its own initiative
- Only after the human confirms does the assistant call `execute_command` with
  `human_confirmed_this_action=True`
- The device runs the command and the tool returns the resulting
  `CommandExecution`, whose `state` field reports the outcome
  (`success`/`error`/`timeout`/`unsync`)
- The returned execution `id` can later be referenced or audited via
  `search_command_executions`

### Example 6: Authoring and Editing MCP-Managed Automation Rules

> ⚠️ `create_rule`, `edit_rule`, and `delete_rule` are **destructive** — they
> modify automation that can execute commands on physical energy hardware. They
> are **disabled by default**. Enable them with
> `--rule-editing-enabled` on the command line or by setting
> `ENAPTER_RULE_EDITING_ENABLED=1`.

MCP-managed rules are automation rules whose lifecycle is managed through the
MCP server. They follow a strict workflow:

1. **Slug prefix.** MCP-managed rules must have a slug starting with the
   reserved prefix `mcp-` (case-sensitive, byte-exact). The prefix is an
   ownership boundary: the assistant may mutate only rules explicitly marked as
   MCP-managed.
2. **Created disabled.** `create_rule` always creates rules disabled, so the
   assistant cannot publish new live automation. A human reviews the rule in the
   Enapter UI and enables it when ready.
3. **Mutate disabled only.** `edit_rule` and `delete_rule` refuse to operate on
   enabled rules, even when the slug has the `mcp-` prefix. If a human enables
   an MCP-managed rule and later wants the assistant to edit or delete it, the
   human must disable it first, ask the assistant, review the result, and
   re-enable in the Enapter UI. This keeps responsibility for live automation
   changes with the human.
4. **No enable tool.** The server does not expose an enable operation. Enabling
   is a human decision made in the Enapter UI.

**User prompt:**

> Create a rule at the Alpha site that logs "battery low" when the battery SOC
> drops below 20%.

**What happens:**

- The assistant creates the rule with `create_rule(site_id="...", slug="mcp-battery-low", script_code="...")`.
  The rule is created disabled and uses runtime version v3.
- The human reviews the rule in the Enapter UI and enables it.

**User prompt (later):**

> Change the threshold in the battery-low rule from 20% to 15%.

**What happens:**

- The assistant calls `read_rule` to get the current script.
- It identifies the exact snippet to change and calls
  `edit_rule(rule_id="...", old_string="battery_soc < 20", new_string="battery_soc < 15")`.
  The edit succeeds only if the old string appears exactly once in the script
  and the rule is currently disabled.
- The human reviews the change and re-enables the rule in the Enapter UI.

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
