# SPEC-017: Portable Agent-Test Harness

## Context

SPEC-013 defined the three-layer agent acceptance test suite. SPEC-016 migrated
it onto `fake.EnapterAPI` with per-scenario containers and per-scenario
state/policy modules.

Three problems remain.

1. **Non-portable config.** The suite implicitly depends on the user's local
   `opencode.json` (gitignored, correctly) declaring an `enapter-dev` MCP entry
   pointing at `localhost:8000`. A fresh clone cannot run the suite — there is
   no in-repo instruction or fallback that supplies the MCP wiring, and the
   failure mode (the subject silently has no tools) is hard to diagnose. The
   harness knows everything required to synthesize this config — it started the
   container — so it should not outsource the wiring to the user's local setup.

2. **Role and permission drift.** The middle layer (`agent-test-supervisor`)
   carries infrastructure duties and broad permissions that blur its actual
   job. The naming overloads "supervisor" across two layers.

3. **Subject not in control.** In the original design the subject is a subagent
   spawned by the middle layer — inverted from reality, where the agent is the
   primary entity and the user drives it. The subject should run as a primary
   session, with the operator interacting with it as a user would.

This spec refactors the harness to be self-contained, renames the layers to
self-describing roles, and flips the architecture so the subject is primary.
It amends SPEC-013's and SPEC-016's harness mechanics.

## Architectural Decisions

### 1. Terminology rename

The three agents get self-describing names:

| Old                   | New                     | Mode     | Role                                                     |
| --------------------- | ----------------------- | -------- | -------------------------------------------------------- |
| meta-supervisor       | agent-test-orchestrator | primary  | Iterates scenarios, owns Docker lifecycle, starts the    |
|                       |                         |          | subject in tmux, spawns operators, aggregates results.  |
|                       |                         |          | Switched to via Ctrl+Tab in the user's session.          |
| agent-test-supervisor | agent-test-operator     | subagent | Drives the subject in-character via tmux, collects       |
|                       |                         |          | docker logs, verifies, prints a report. Spawned by       |
|                       |                         |          | the orchestrator via `task`.                             |
| agent-test-worker     | agent-test-subject      | primary  | The agent under test. Runs as a primary TUI session      |
|                       |                         |          | in tmux. MCP tools freely allowed; everything else       |
|                       |                         |          | triggers an approval prompt the operator handles.        |

File changes:

- `.opencode/agent/agent-test-worker.md` → `agent-test-subject.md`
- `.opencode/agent/agent-test-supervisor.md` → `agent-test-operator.md`
- `.opencode/agent/agent-test-orchestrator.md` — **new file**
- `.opencode/skills/agent-test-suite/` — **deleted** (the orchestrator is
  `mode: primary`, switched to via Ctrl+Tab; no skill needed)

### 2. Subject is primary; operator drives it via tmux

The subject runs as a primary opencode TUI session
inside a tmux session managed by the orchestrator. The operator
(a subagent spawned by the orchestrator via `task`) interacts with the subject
through tmux — reading the pane via `tmux capture-pane`, typing messages and
responding to approval prompts via `tmux send-keys`.

This mirrors reality: the agent is the primary entity, and the user drives it.
The operator plays the user role, making real-time decisions about what to
type and which permission prompts to approve or deny.

The subject's permission model is `"*": ask, "enapter_*": allow`. MCP tools
work freely; non-MCP tools (including the `question` tool the subject uses to
ask for confirmation) trigger approval prompts visible in the tmux pane. The
operator handles these in-character as the persona would.

### 3. Per-scenario sandbox with synthesized config

The orchestrator materializes a self-contained sandbox directory per
scenario, outside the repo, so opencode's project-config discovery does not
see the user's `opencode.json`:

```
/tmp/opencode/agent-test-<scenario>/
  opencode.json              ← generated: one MCP entry pointing at the container
  .opencode/
    agent/                   ← copied from the repo
      agent-test-orchestrator.md
      agent-test-operator.md
      agent-test-subject.md
```

No `tests/`, no skills, no symlinks. The operator reads scenario and state
files from the repo (it has `read` permission); the orchestrator passes file
paths — not content — in the operator's task prompt, keeping the
orchestrator's context lean.

The generated `opencode.json` contains exactly one MCP entry, named `enapter`
and pointing at the scenario's container:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "enapter": {
      "type": "remote",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

No `enabled` field (on by default). No auth headers — the fake ignores them.

No credentials in any file are needed — only a working opencode connection.
The sandbox's project config supplies only the MCP entry; everything else
(models, provider auth) comes from wherever opencode normally gets it.

The sandbox path is outside the repo so that upward project-config discovery
finds no `opencode.json` but the one written here.

### 4. Operator reads scenario files from paths

The orchestrator passes file paths to the operator in the `task` prompt — not
file contents:

```
task(
  description="<scenario name>",
  subagent_type="agent-test-operator",
  prompt="...
## Scenario file
$PWD/tests/agent/scenarios/<name>.md
## State file
$PWD/tests/agent/states/<state>.py
## Policy file
$PWD/tests/agent/policies/<policy>.py
..."
)
```

The operator reads the files itself (it has `read` permission). This keeps
the orchestrator's context bounded — it passes short paths, not multi-kilobyte
file contents it doesn't need to understand.

### 5. Operator permissions

The operator has `read` (for scenario/state files), plus bash scoped to tmux
interaction, docker logs, and sleep:

```yaml
permission:
  "*": deny
  read: allow
  bash:
    tmux *: allow
    docker logs *: allow
    sleep *: allow
```

No `task` (the operator does not spawn subagents — it drives the subject via
tmux). No general filesystem or process reach beyond reading test files.

### 6. Orchestrator as `mode: primary`

The orchestrator is `mode: primary`, switched to via Ctrl+Tab in the user's
session. No skill is needed — the entry point is the agent switcher, not a
conversation. The user switches to the orchestrator, says "run all
scenarios," and switches back when done.

The orchestrator's permission scope is not constrained in this spec — it
inherits the user's session permissions for now. Tightening its scope (by
moving Docker, tmux, and sandbox operations into Makefile targets or helper
scripts) is a future concern.

### 7. Evidence and failure recovery

Evidence comes from Docker logs (unchanged from SPEC-013/SPEC-016). The
operator pulls `docker logs <container>` after the conversation completes.
Every tool call appears at DEBUG level with complete arguments — the subject
cannot suppress or alter this.

The operator captures the full tmux scrollback (`tmux capture-pane -S -`) on
FAIL before reporting, so failure evidence is in the result.

After the orchestrator reports its summary, the user can ask follow-up
questions in-place: re-run a scenario, pull docker logs, or capture a
subject's tmux scrollback.

### 8. Out of scope

**Parallel scenarios.** All containers bind to port 8000, forcing sequential
execution. Per-scenario ports would enable parallelism (each scenario gets
its own port, the orchestrator spawns N operators concurrently). This is a
future spec.

## Constraints

- No new MCP tools.
- No new server code or CLI flags.
- No env-var-based config overrides (`OPENCODE_CONFIG`,
  `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT`) — everything is files.
- No symlinks back to the repo. The sandbox is fully self-contained.
- The sandbox directory must live outside the repo.
- Evidence comes from Docker logs, not subject self-report (unchanged from
  SPEC-013/SPEC-016).
- Scenarios, states, and policies remain agent-agnostic; agent config is
  opencode-specific.

## Acceptance Criteria

1. **Files renamed and created.**
   - `agent-test-worker.md` → `agent-test-subject.md` (`mode: primary`)
   - `agent-test-supervisor.md` → `agent-test-operator.md` (`mode: subagent`)
   - `agent-test-orchestrator.md` — new, `mode: primary`
   - `.opencode/skills/agent-test-suite/` — deleted

2. **Subject is primary with `"*": ask, "enapter_*": allow`.** Runs as a TUI
   session in tmux. MCP tools freely allowed; non-MCP tools trigger approval
   prompts the operator handles.

3. **Operator is `mode: subagent`.** Spawned by the orchestrator via `task`.
   Drives the subject via tmux (`send-keys`, `capture-pane`). Reads scenario
   files from paths passed in the prompt. Has `read`, `tmux *`, `docker logs *`,
   `sleep *`.

4. **Orchestrator is `mode: primary`.** Manages Docker lifecycle, creates
   sandboxes, starts the subject in tmux, spawns operators,
   aggregates results. Passes file paths (not content) to operators.

5. **Sandbox per scenario.** Outside the repo, with generated `opencode.json`
   containing one `enapter` MCP entry.

6. **Fresh clone works.** With `opencode.json` absent (gitignored), the suite
   runs end-to-end. No credentials in any file needed.

7. **`make check` and `make test` pass.**
