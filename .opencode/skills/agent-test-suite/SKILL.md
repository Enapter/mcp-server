---
name: agent-test-suite
description: Agent-driven acceptance test suite for the Enapter MCP server. Use when asked to run agent tests, validate MCP tool usability, or run acceptance tests.
---

# Agent Acceptance Test Suite

Validates whether an AI agent can discover and correctly use the MCP server's
tools to accomplish a real task. Unit tests verify mechanics; only a real agent
interaction verifies usability.

## Why three layers

The worker — the agent under test — must reach the MCP server through its tools.
In opencode a subagent inherits MCP servers from its parent session, so the
chain is fixed:

- The **worker** (subagent) gets the `enapter-dev` MCP server only if its parent
  has it.
- The **orchestrator** (the worker's parent, a separate `opencode run` inside
  tmux) has it only if its own session connected to the server at startup.
- An opencode session connects to `enapter-dev` at `localhost:8000` when it
  starts — so the server **must already be running** when the orchestrator
  launches.
- Only the **meta-supervisor** (this session) can guarantee that. It owns the
  Docker lifecycle. The orchestrator cannot start the server it depends on.

Per-scenario state: each scenario needs its own fake backend (a `state` module,
plus an optional `policy` module), selected by a `fake://` URL. So the
meta-supervisor starts a fresh container per scenario, launches a fresh
orchestrator (which connects to that container), lets it run, and tears down.

## Roles

1. **Meta-supervisor** (you) — iterate scenarios: for each, start its server
   container, launch the orchestrator, wait for it to finish, capture the
   result, tear the container down. Aggregate and report.
2. **Orchestrator** (`agent-test-supervisor`, one launch per scenario, inside
   tmux) — spawn the worker, drive the conversation in-character, collect Docker
   logs, verify outcomes against the scenario, print the result. It does NOT
   manage containers.
3. **Worker** (`agent-test-worker`, subagent) — a black box with access ONLY to
   the MCP tools. No filesystem, no shell, no source code.

## Variables

Persist across bash calls:

```bash
SESSION=enapter-mcp-server-agent-test
CONTAINER_PREFIX=enapter-mcp-server-agent-test
```

## Step 1: Build the Docker image

```bash
docker image inspect enapter/mcp-server:dev >/dev/null 2>&1 || make docker-image
```

Rebuild if server or CLI source changed since the last run.

## Step 2: Create the tmux session

One session, reused across scenarios:

```bash
tmux kill-session -t $SESSION 2>/dev/null || true
tmux new-session -d -s $SESSION -x 200 -y 50
```

## Step 3: Run each scenario

List the scenarios, then loop. For each `tests/agent/scenarios/<name>.md`:

### 3a. Read the scenario's frontmatter

Read the scenario file's YAML frontmatter (between the `---` markers). It holds
`state` (required dotted module path) and optionally `policy`. Build the
`fake://` URL: with a policy, `fake://?policy=<policy>&state=<state>`; without,
`fake://?state=<state>`. If a scenario has no frontmatter, record it as errored
and continue.

### 3b. Start the scenario's container

```bash
CONTAINER="$CONTAINER_PREFIX-<name>"
docker stop "$CONTAINER" 2>/dev/null || true
docker rm "$CONTAINER" 2>/dev/null || true
```

```bash
docker run -d --name "$CONTAINER" \
  -p 8000:8000 \
  -v "$PWD/tests:/app/tests:ro" \
  enapter/mcp-server:dev \
  -v serve \
    --enapter-http-api-url "<fake:// URL>" \
    --rule-editing-enabled 1 \
    --command-execution-enabled 1
```

Confirm it is running:

```bash
sleep 2
docker ps --filter "name=$CONTAINER" --filter "status=running" --format "{{.Names}}"
```

If empty, the server failed — capture `docker logs "$CONTAINER"`, record the
scenario as errored, and continue.

### 3c. Launch the orchestrator for this one scenario

```bash
tmux send-keys -t $SESSION "opencode run --agent agent-test-supervisor 'Run the scenario at tests/agent/scenarios/<name>.md'" Enter
```

The orchestrator connects to `localhost:8000` (the container above) at startup;
the worker it spawns inherits that connection.

### 3d. Wait for it to finish

Poll until the orchestrator prints its result and returns to the shell prompt:

```bash
tmux capture-pane -t $SESSION -p
```

Poll on short intervals. The result is a PASS/FAIL block for the scenario.

### 3e. Capture the result, then tear down the container

```bash
tmux capture-pane -t $SESSION -p
docker stop "$CONTAINER" || true
docker rm "$CONTAINER" || true
```

Repeat 3a–3e for the next scenario.

## Step 4: Report and clean up

Aggregate the per-scenario results into a summary (X/Y passed) for the user.
Then tear down the session and any leftover container:

```bash
tmux kill-session -t $SESSION 2>/dev/null || true
docker ps -a --filter "name=$CONTAINER_PREFIX" --format "{{.Names}}" | xargs -r docker rm -f
```
