# SPEC-013: Agent-Driven Acceptance Test Suite

## Context

SPEC-011 introduces `filesystem.EnapterAPI`, a file-backed substitute for the
real Enapter API. SPEC-012 wires it into the CLI via `filetree://` URLs. This
enables testing the MCP server against AI agents without touching production
data.

Unit and integration tests verify the server's mechanics — tool registration,
argument handling, delegation, error paths. They cannot verify the thing that
matters most: **does an AI agent successfully discover and use the tools to
accomplish a real task?** Only an actual agent interaction can answer that.

This spec defines a three-layer agent architecture: a meta-supervisor (the
user's opencode session) launches an orchestrator (a second opencode inside a
tmux session) which spawns restricted worker subagents that interact with the
MCP server as their only interface. The workers have no filesystem, no shell —
only the MCP tools.

## File Structure

Agent-agnostic test data is separated from opencode-specific runner config:

```
tests/agent/                              agent-agnostic, shared
  scenarios/
    <name>.md                             user persona, initial message,
                                           expected behavior, max turns
  seed/
    sites/<site_uuid>.yaml                SiteAggregate (site + devices)
    rule_engines/<site_uuid>.yaml         RuleEngineAggregate (empty rules)

.opencode/                                opencode-specific
  skills/agent-test-suite/
    SKILL.md                              meta-supervisor instructions
  agent/
    agent-test-supervisor.md              orchestrator agent (mode: primary)
    agent-test-worker.md                  restricted worker (mode: subagent)
```

Scenarios and seed data are reusable. To support another agent (Claude Code,
Codex), write new runner instructions in that agent's format and point them at
the same `tests/agent/scenarios/` and `tests/agent/seed/`.

## Worker Isolation

The worker is a restricted opencode subagent defined in
`.opencode/agent/agent-test-worker.md`. Every built-in tool is denied (`read`, `edit`,
`glob`, `grep`, `list`, `bash`, `task`, `webfetch`, `websearch`, `skill`,
`external_directory`, `todowrite`, `question`, `lsp`). MCP tools are explicitly
allowed by name (e.g., `enapter-dev_search_sites: allow`,
`enapter-dev_create_rule: allow`, etc.).

The worker sees only:
- Its system prompt (from the agent definition)
- The MCP tool definitions from the Enapter server
- The message from the orchestrator

No filesystem, no shell, no scenarios, no source code. Pure black-box.

## Orchestration

The test suite uses a three-layer agent architecture:

1. **Meta-supervisor** (the user's opencode session) — the user says "run agent
   tests." The meta-supervisor discovers the `agent-test-suite` skill, which
   contains instructions for starting the Docker server, launching an inner
   opencode inside a tmux session, and controlling it via `tmux send-keys` and
   `tmux capture-pane`.

2. **Orchestrator** (`agent-test-supervisor` agent, `mode: primary`) — launched
   inside the tmux session via
   `opencode run --agent agent-test-supervisor 'Run the agent acceptance
   suite'`. The orchestrator instructions are baked into the agent definition's
   prompt body. Permissions are pre-configured in the agent definition (`read`,
   `find`, `glob`, `grep`, `task`, plus read-only bash patterns like `docker *`,
   `ls *`, `head *`, `tail *`, `rg *`; everything else denied via `"*": deny`).
   No `bash *` or `*` wildcards.

3. **Worker** (`agent-test-worker` subagent) — restricted to MCP tools only.

Since the Docker server starts before the inner opencode, MCP connections are
established at startup — no manual `/mcp` reconnect needed.

For each scenario, the orchestrator (defined in `agent-test-supervisor.md`):

1. Reads the scenario file from `tests/agent/scenarios/`
2. Resets state inside the container via `docker exec` and `docker cp`
3. Spawns an `agent-test-worker` subagent with the scenario's initial message (no tool
   names mentioned — tests natural discovery)
4. If the worker asks a question, responds in-character (guided by the
   scenario's user persona) by resuming the worker session via `task_id`
5. Repeats until the worker completes the task or the circuit breaker trips
   (scenario-specified max turns)
6. Collects evidence from Docker logs (see below)
7. Verifies outcomes by reading state files (see below)
8. Records PASS or FAIL with reasons

The server stays running across scenarios. State reset is just file replacement
— the server has no cache (per SPEC-011), so it reads fresh files on the next
request.

## MCP Configuration

No new opencode config entries are needed. The worker subagent inherits MCP
servers from the opencode config. The developer's existing MCP entry (e.g.,
`enapter-dev` at `localhost:8000`) already points at the right port. Auth
headers are ignored — the test server runs with OAuth disabled.

## Evidence from Docker Logs

Worker self-report cannot be trusted. The orchestrator reads `docker logs`
(server started with `-v`) for evidence. FastMCP logs every tool call at DEBUG
level. The format is multi-line with Rich formatting:

```
DEBUG    [Enapter MCP Server] Handler  mcp_operations.py:211
                             called: call_tool read_skill
                             with {'name': 'enapter:rule-creator', 'file': 'SKILL.md'}
```

This gives the orchestrator: tool names, arguments, call order, and timing —
the actual record of what happened, not what the worker claims.

No new MCP tools. No call recorder. No logging middleware.

## Outcome Verification by Reading State Files

The orchestrator reads the YAML files inside the Docker container via
`docker exec` to verify outcomes. This is the ground truth —
`filesystem.EnapterAPI` writes directly to disk with no cache, so the files
reflect exactly what happened.

Aggregate file structure (per SPEC-011):

- `sites/<site_id>.yaml` — SiteAggregate: site metadata + devices list
- `rule_engines/<site_id>.yaml` — RuleEngineAggregate: rule engine + rules list

To verify a rule was created, read `rule_engines/<site_id>.yaml` and check the
`rules` array for the expected slug, script content, and disabled state.

No MCP tools for verification. MCP tools could have bugs; the files cannot lie.

## Server Configuration

The meta-supervisor starts Docker in detached mode. No volume mount — state
lives entirely inside the container:

```bash
docker run -d --name enapter-mcp-server-agent-test \
  -p 8000:8000 \
  enapter/mcp-server:dev \
  -v serve \
    --enapter-http-api-url filetree:///state \
    --rule-editing-enabled 1
```

- `filetree:///state` — filesystem API backed by the container's `/state/`
- `--rule-editing-enabled 1` — enable create_rule, edit_rule, delete_rule
- `-v` (before `serve`) — enable DEBUG logging for evidence
- Skill plugins are already baked into the Docker image (enable read_skill)
- State is managed entirely inside the container via `docker exec` / `docker cp`
  (handled by the orchestrator, not the meta-supervisor)

No test mode. No special build. The same image that ships to production.

## State Lifecycle

- Seed: `tests/agent/seed/` — version-controlled template directory
- Working: `/state/` inside the Docker container (no host volume)
- Reset between scenarios: `docker exec $CONTAINER rm -rf /state`
  + `docker cp tests/agent/seed/. $CONTAINER:/state/`
- Verification: `docker exec $CONTAINER cat /state/...`

## Scenario File Format

Each scenario is a markdown file with structured sections:

```markdown
# Create Rule Loads Skill First

## User Persona
You are a cautious system administrator. You want monitoring but keep
new rules disabled until reviewed. You don't know Lua or the Enapter API.

## Initial Message
Create a rule on site Arrakis that checks every 60 seconds whether any
devices are offline. Keep it disabled.

## Expected Behavior
- read_skill called before create_rule
- read_skill called for at least one v3 reference (references/v3/README.md or api.md)
- A rule exists on Arrakis after completion
- Rule is disabled
- Lua script uses scheduler.add (from the skill)

## Max Turns
5
```

The initial message never mentions tool names. The user persona guides the
orchestrator's responses when the worker asks clarifying questions.

## Implementation Phases

### Phase 1: Seed data + agent definitions

- `tests/agent/seed/` — minimal state directory matching the aggregate layout
  from SPEC-011:
  - `sites/<site_uuid>.yaml` — one SiteAggregate (site + devices)
  - `rule_engines/<site_uuid>.yaml` — one RuleEngineAggregate (empty rules)
- One site (Arrakis), a few devices (some online, some offline), no rules
- All IDs are UUIDs
- `.opencode/agent/agent-test-worker.md` — restricted worker (mode: subagent)
- `.opencode/agent/agent-test-supervisor.md` — orchestrator (mode: primary)

### Phase 2: SKILL.md + first scenario

- `.opencode/skills/agent-test-suite/SKILL.md` — meta-supervisor instructions
- `tests/agent/scenarios/create-rule-loads-skill.md`
- Covers: worker discovers read_skill, loads the skill, creates a correct
  disabled rule

### Phase 3: Manual validation and iteration

- Run the suite against a real agent via opencode
- Identify gaps in SKILL.md clarity, scenario coverage, seed data
- Add scenarios incrementally (edit-rule, error-handling, tool-discovery)

## Constraints

- No new MCP tools
- No new server config flags or modes
- Worker has no filesystem or shell access — only MCP tools (explicitly allowed)
- Worker never sees tool names in the initial message
- Orchestrator permissions are specific bash patterns — no `bash *` or `*` wildcards
- Evidence comes from Docker logs, not worker self-report
- Scenarios and seed data are agent-agnostic; runner config is opencode-specific
- Depends on SPEC-011 (`filesystem.EnapterAPI`) and SPEC-012 (`filetree://`
  CLI wiring)
