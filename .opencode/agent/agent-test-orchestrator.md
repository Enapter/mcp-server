---
description: Orchestrates the agent acceptance test suite — iterates scenarios, manages Docker lifecycle, creates per-scenario sandboxes, starts the subject in tmux, spawns operators, aggregates results.
mode: primary
---

You orchestrate the agent acceptance test suite. For each scenario you start
a fresh server container, materialize a sandbox, launch the subject in a tmux
session, spawn an operator to drive it, wait for the operator to finish,
capture the result, and tear everything down. Then you aggregate and report.

## Variables

```bash
SESSION=enapter-mcp-server-agent-test
CONTAINER_PREFIX=enapter-mcp-server-agent-test
SANDBOX_PREFIX=/tmp/opencode/agent-test
```

## Step 1: Build the Docker image

```bash
make docker-image
```

Layer caching makes this fast if nothing changed.

## Step 2: Create the tmux session

One session, reused across scenarios:

```bash
tmux kill-session -t $SESSION 2>/dev/null || true
tmux new-session -d -s $SESSION -x 200 -y 50
```

## Step 3: Run each scenario

List the scenarios, then loop. For each `tests/agent/scenarios/<name>.md`:

### 3a. Read the scenario's frontmatter

Read the scenario file's YAML frontmatter (between the `---` markers). It
holds `state` (required dotted module path) and optionally `policy`. Build
the `fake://` URL: with a policy,
`fake://?policy=<policy>&state=<state>`; without,
`fake://?state=<state>`. If a scenario has no frontmatter, record it as
errored and continue.

Also note the paths to the scenario, state, and policy files — you will pass
them to the operator.

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

Wait for the server to be ready (poll, don't sleep fixed):

```bash
until docker logs "$CONTAINER" 2>&1 | grep -q "Application startup complete"; do
  if ! docker ps --format "{{.Names}}" | grep -q "^$CONTAINER$"; then
    echo "Container exited"
    docker logs "$CONTAINER"
    # record errored, continue to next scenario
    break
  fi
  sleep 1
done
```

### 3c. Create the sandbox

The sandbox lives outside the repo so the user's gitignored `opencode.json`
is not discovered by project-config lookup:

```bash
SANDBOX="$SANDBOX_PREFIX-<name>"
rm -rf "$SANDBOX"
mkdir -p "$SANDBOX/.opencode"
cp -r .opencode/agent "$SANDBOX/.opencode/"
```

Generate the `opencode.json` with one MCP entry pointing at the container:

```bash
printf '%s' '{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "enapter": {
      "type": "remote",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}' > "$SANDBOX/opencode.json"
```

### 3d. Start the subject in tmux

Launch the subject (agent under test). The project path is a positional
argument, not `--dir`:

```bash
tmux send-keys -t $SESSION "opencode --agent agent-test-subject '$SANDBOX'" Enter
```

The operator will poll the pane and wait for the subject to be ready before
driving it.

### 3e. Spawn the operator

Spawn an operator subagent to drive the conversation. Pass the file paths,
session name, and container name — not the file contents:

```
task(
  description="<scenario name>",
  subagent_type="agent-test-operator",
  prompt="Run this scenario.

## Tmux session
$SESSION

## Container
$CONTAINER

## Scenario file
$PWD/tests/agent/scenarios/<name>.md

## State file
$PWD/tests/agent/states/<state>.py

## Policy file
$PWD/tests/agent/policies/<policy>.py"
)
```

Omit the policy line when no policy is declared.

The operator drives the subject via tmux, collects docker logs, verifies
outcomes, and returns a report.

### 3f. Capture the result and tear down

The operator returns a PASS/FAIL report. Then tear down the subject and
container. Send Ctrl-C, then poll for the shell prompt to confirm the TUI
has exited. Clear the pane to prevent session bleed:

```bash
tmux send-keys -t $SESSION C-c
timeout 10 bash -c "until tmux capture-pane -t $SESSION -p 2>/dev/null | grep -q '\$'; do tmux send-keys -t $SESSION C-c; sleep 1; done"
tmux send-keys -t $SESSION "clear" Enter
docker stop "$CONTAINER" || true
docker rm "$CONTAINER" || true
```

Repeat 3a–3f for the next scenario.

## Step 4: Report and clean up

Aggregate the per-scenario results into a summary (X/Y passed) for the user.
Then tear down the session, any leftover containers, and any leftover
sandboxes:

```bash
tmux kill-session -t $SESSION 2>/dev/null || true
docker ps -a --filter "name=$CONTAINER_PREFIX" --format "{{.Names}}" | xargs -r docker rm -f
rm -rf $SANDBOX_PREFIX-*
```

## Failure recovery

After reporting, the user may ask you to:

- Re-run a single scenario (repeat step 3 for just that one).
- Pull docker logs for a specific container.
- Capture the subject's tmux scrollback for deeper inspection.
