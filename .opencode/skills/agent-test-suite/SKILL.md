---
name: agent-test-suite
description: Agent-driven acceptance test suite for the Enapter MCP server. Use when asked to run agent tests, validate MCP tool usability, or run acceptance tests.
---

# Agent Acceptance Test Suite

Three-layer agent architecture:

1. **Meta-supervisor** (you, the user's opencode session) — starts server,
   launches the orchestrator inside a tmux session, controls it via tmux, reports
   results to the user
2. **Orchestrator** (`agent-test-supervisor` agent inside tmux) — runs
   scenarios, spawns workers, collects evidence, verifies outcomes
3. **Worker** (`agent-test-worker` subagent) — restricted to MCP tools only, black-box

## Workflow

Set up variables (these persist across bash calls):

```bash
CONTAINER=enapter-mcp-server-agent-test
SESSION=enapter-mcp-server-agent-test-supervisor
```

### Step 1: Start the test server

Build the Docker image if it doesn't exist:

```bash
docker image inspect enapter/mcp-server:dev >/dev/null 2>&1 || make docker-image
```

Start the server (no volume mount — state lives inside the container):

```bash
docker stop $CONTAINER 2>/dev/null || true
docker rm $CONTAINER 2>/dev/null || true
docker run -d --name $CONTAINER \
  -p 8000:8000 \
  enapter/mcp-server:dev \
  -v serve \
    --enapter-http-api-url filetree:///state \
    --rule-editing-enabled 1
```

Wait briefly for the server to start, then verify:

```bash
docker ps --filter name=$CONTAINER --filter status=running -q | grep -q . \
  || (echo "Server failed to start" && docker logs $CONTAINER && exit 1)
```

### Step 2: Launch the orchestrator

Launch opencode with the `agent-test-supervisor` agent and the test prompt in
one command:

```bash
tmux kill-session -t $SESSION 2>/dev/null || true
tmux new-session -d -s $SESSION -x 160 -y 50
tmux send-keys -t $SESSION "opencode run --agent agent-test-supervisor 'Run the agent acceptance test suite'" Enter
```

### Step 3: Monitor

Check periodically until the suite completes. The orchestrator runs autonomously
— it reads scenarios, spawns `agent-test-worker` subagents, collects evidence
from Docker logs, verifies state files, and produces a report.

Watch for:
- **Suite completion** — the orchestrator will output a summary and stop
- **Errors** — if the orchestrator stalls or crashes, inspect the output and
  intervene

```bash
tmux capture-pane -t $SESSION -p
```

Repeat until the suite is complete, then proceed to Step 4. Prefer polling
often (shorter intervals) over longer suite execution — don't let the
orchestrator wait idle while you sleep.

### Step 4: Report and clean up

Capture the final output for the user, then clean up:

```bash
tmux capture-pane -t $SESSION -p
tmux kill-session -t $SESSION
docker stop $CONTAINER
docker rm $CONTAINER
```
