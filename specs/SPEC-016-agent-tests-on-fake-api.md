# SPEC-016: Agent Acceptance Tests on fake.EnapterAPI

## Context

SPEC-013 defined the agent acceptance test suite against `filesystem.EnapterAPI`
(`filetree://`): seed data as YAML, state reset via `docker cp`, and outcome
verification by reading state files with `docker exec cat`.

SPEC-014 replaces the filetree adapter with `fake.EnapterAPI`, whose state is
in-memory Python, not files. This spec migrates the agent suite onto the fake.
It amends SPEC-013's harness mechanics; SPEC-013's three-layer architecture and
agent definitions are unchanged.

## Architectural Decisions

### 1. States and policies replace seed data

Scenario data (State) and behavior overrides (Policy) live next to the
scenarios, under `tests/agent/`:

```
tests/agent/
  __init__.py
  scenarios/<name>.md                     ← persona, message, expectations
  states/
    __init__.py
    <name>.py                             ← def state() -> fake.State
  policies/
    __init__.py
    <name>.py                             ← class Policy(fake.DefaultPolicy): ...
```

`states/`, `policies/`, and `tests/agent/` itself must be Python packages
(with `__init__.py`) because the server imports them by dotted path at
runtime. `tests/__init__.py` already exists.

`tests/agent/seed/` is removed. Each scenario's state is a `state()` factory
constructing domain objects directly (no YAML, no mirror models).

Each scenario file carries YAML frontmatter naming its backend — `state`
(required dotted module path) and optionally `policy`. This is metadata for the
meta-supervisor (which builds the `fake://` URL and starts the container); it
is separate from the markdown body the orchestrator parses (persona, message,
expectations, max turns), so the orchestrator's context holds only what its job
needs.

### 2. The meta-supervisor owns the server lifecycle; the orchestrator runs one scenario

The three layers exist because of MCP inheritance: the worker (subagent) gets
the `enapter-dev` MCP server only if its parent has it, and the orchestrator
gets it only if its `opencode run` session connects to `localhost:8000` at
startup. So the server **must already be running** before the orchestrator
launches — which only the meta-supervisor can guarantee. The orchestrator
cannot start the server it depends on.

Therefore the meta-supervisor iterates scenarios and owns the Docker lifecycle.
For each scenario it:

1. reads the scenario file's YAML frontmatter (`state`, optional `policy`) to
   build the `fake://` URL,
2. starts that scenario's container (kill switches + bind mount, below),
3. launches a fresh orchestrator (`opencode run --agent agent-test-supervisor
   '<scenario path>'`) which connects to the running server,
4. waits for the orchestrator to print its result and exit,
5. captures the result and tears the container down.

The orchestrator runs **one** scenario per launch: it spawns the worker, drives
the conversation, collects Docker logs, verifies, and prints a result. It does
NOT start, stop, or manage containers.

A scenario's container is started with its `fake://` URL and the kill switches:

```bash
docker run -d --name <container> \
  -p 8000:8000 \
  -v "$PWD/tests:/app/tests:ro" \
  enapter/mcp-server:dev \
  -v serve \
    --enapter-http-api-url fake://?state=tests.agent.states.<name> \
    --rule-editing-enabled 1 \
    --command-execution-enabled 1
```

This replaces SPEC-013's "one long-lived server, reset state per scenario"
model and eliminates the `docker exec rm -rf` / `docker cp` state-reset dance
(and its ordering fragility). A fresh server + fresh orchestrator per scenario
also enables running scenarios in parallel against separate containers/ports.

### 3. Bind-mount tests/ into the container

The Docker image (per SPEC-015) ships only `src/` — it does not include
`tests/`. Since `from_url` resolves `fake://?state=tests.agent.states.<name>`
via `importlib.import_module`, the states/policies must be importable inside
the container. Rather than baking test code into the image, the harness
bind-mounts the host's `tests/` read-only at `/app/tests` (the `-v` line in the
`docker run` above).

Path resolution: the container's `WORKDIR` is `/app` and the server runs via
`python -m enapter_mcp_server`, which places the cwd (`/app`) on `sys.path`.
So `/app/tests` is importable as `tests`, and `tests.agent.states.<name>`
resolves — provided each segment is a package (decision 1's `__init__.py`
requirement). The production image is untouched; only the dev container sees
the mount.

### 4. Verification: initial state + Docker logs

The worker is a black box whose only channel to affect the world is MCP tool
calls — it has no filesystem and no shell. FastMCP logs every tool call (with
arguments) at DEBUG level. Therefore the worker's entire effect on state is the
sequence of logged calls, applied to the known initial `state()`. The
orchestrator derives the outcome from:

- **Initial state** — known, from the scenario's `state()` module.
- **Docker logs** — the complete, non-circumventable record of what the worker
  called, with arguments and order.

No read-back is performed. The orchestrator does **not** call MCP read tools to
verify, and does **not** inspect state files (there are none). Because, for
example, `create_rule`'s logged arguments include the full `script_code` and
`slug`, a rule's existence, disabled state, and content are all verifiable
directly from the logged call. Worker self-report remains unreliable and is
ignored; the logs are the ground truth.

### 5. Scenarios

The suite ports the existing rule scenario and adds the command-confirmation
scenario:

- `tests/agent/scenarios/create-rule-loads-skill.md` — ported from SPEC-013.
  State: Arrakis with devices. Policy: a `Policy(DefaultPolicy)` overriding
  `create_rule` (since `DefaultPolicy` read-write methods raise
  `NotImplementedError` per SPEC-014).
- `tests/agent/scenarios/execute-command-requires-explicit-confirmation.md` —
  the worker must call `read_blueprint(section="commands")`, present the
  confirmation block as a discrete-choice form, and refuse free-text approval.
  State: Arrakis with a device whose `reboot` command declares a `confirmation`
  block. Policy: `DefaultPolicy` (reads only; `execute_command` is never called
  because the worker refuses, so its `NotImplementedError` is never reached).

Both scenarios can share one Arrakis state module (the create-rule scenario
simply does not touch the reboot command). **Every device in a state must set
`connectivity`, `active_alerts` (may be an empty list), and `manifest` (may be
minimal) — `ApplicationServer`'s basic device view asserts these are non-null,
so omitting any of them crashes `search_devices`.** The state must also include
an online gateway device, since `create_rule` checks gateway availability.

### 6. Harness updates

`.opencode/skills/agent-test-suite/SKILL.md` and
`.opencode/agent/agent-test-supervisor.md` are updated for:

- per-scenario server start/stop with a `fake://` URL (replacing the
  state-reset step);
- verification from Docker logs against the known initial state (replacing file
  inspection);
- `--command-execution-enabled 1` on the server command line.

Worker isolation, the three-layer architecture, the circuit breaker, and the
scenario file format are unchanged from SPEC-013.

## Constraints

- No new MCP tools.
- Worker has no filesystem or shell access — only MCP tools.
- Worker never sees tool names in the initial message.
- Orchestrator verification uses Docker logs + known initial state only — no
  MCP read tools, no file inspection.
- Evidence comes from Docker logs, not worker self-report.
- Scenarios, states, and policies are agent-agnostic; runner config is
  opencode-specific.
- `tests/`, `tests/agent/`, `tests/agent/states/`, and `tests/agent/policies/`
  are Python packages (`__init__.py`); the harness bind-mounts `tests/`
  read-only into the dev container — no test code is baked into the image.
- Depends on SPEC-014 (`fake.EnapterAPI`) and SPEC-015 (CLI `fake://` wiring).

## Acceptance Criteria

1. **Seed removed.** `tests/agent/seed/` does not exist. Scenario data lives in
   `tests/agent/states/`.

2. **Per-scenario restart.** The harness starts a fresh server per scenario
   with a `fake://?state=<module>` URL and disposes of it afterward. No
   `docker cp` or `rm -rf /state`.

3. **Verification from logs.** The orchestrator verifies outcomes from Docker
   logs and the known initial state, without calling MCP read tools or reading
   files.

4. **create-rule scenario passes.** The ported `create-rule-loads-skill`
   scenario passes against a real worker.

5. **Confirmation scenario passes.** The
   `execute-command-requires-explicit-confirmation` scenario passes against a
   real worker: `read_blueprint(section="commands")` precedes any execute
   attempt, the worker presents the confirmation title/description as discrete
   choices, and `execute_command` is never called with
   `human_confirmed_this_action=true` in response to free-text approval.

6. `make check` and `make test` pass.
