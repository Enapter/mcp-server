# SPEC-007: Command Execution

## Context

The MCP server has so far been read-only: every tool is registered with
`readOnlyHint=True` and only reads sites, devices, telemetry, blueprints, rules,
and the command-execution *history* (`search_command_executions`). The upstream
Enapter API can already execute commands on physical devices, and the
access-control model (SPEC-001/002/003) already defines who may execute what.
What is missing is a tool that actually executes a command — and because Enapter
devices are real-world energy hardware (pumps, electrolysers, valves, inverters),
acting on the world has physical consequences. This spec adds command execution
behind layered defenses so the server can act safely.

The upstream `enapter.http.api.commands.Client` exposes two execution
primitives:

- `execute(device_id, name, arguments)` — **blocking**: returns when the command
  completes or the upstream's own timeout fires (which yields the terminal
  `timeout` state).
- `create_execution(device_id, name, arguments)` — **fire-and-forget**: returns a
  tracked execution immediately; pollable via `get_execution`.

We use the blocking `execute` primitive — one call that returns when the command
completes. This is deliberately simple. The fire-and-forget `create_execution`
plus a poll loop (and with it, progress logging) is a possible future evolution,
deferred until production usage justifies the complexity (see Decision 8).

## Architectural Decisions

### 1. Opt-in kill switch, default OFF

Command execution is dangerous, so the `execute_command` tool is registered
**only** when the server is explicitly configured to allow it
(`ServerConfig.command_execution_enabled`, driven by
`ENAPTER_COMMAND_EXECUTION_ENABLED` / `--command-execution-enabled`, default
`"0"`). All existing deployments stay read-only with zero changes. This is the
reliable, deployment-level off switch — it does not depend on client behavior.

### 2. Single synchronous tool using the blocking `execute` primitive

`execute_command` is one tool. It calls
`commands.execute(device_id, name, arguments)`, which blocks until the command
finishes or the upstream's own timeout fires (yielding the terminal `timeout`
state), then returns the `Execution`, which we map to `CommandExecution` and
return. There is no `wait` argument, no second tool, no server-side poll loop, no
`ctx` parameter, and no progress logging. We keep v1 deliberately simple and will
revisit based on production usage.

The backend owns the command-level timeout; the MCP client owns the HTTP-call
timeout. If the client cancels or times out the call before it returns, the agent
recovers the outcome via the existing `search_command_executions` by
`device_id`/time (the agent has no `id` in that case). We make no claim about
whether the device command continues after a client cancellation — that is the
upstream's behaviour, not ours.

### 3. Return `CommandExecution`; let the SDK raise

Three cases, cleanly separating "we refused / the call failed to submit" (raise)
from "the command ran, here is its outcome" (a result, possibly an error state):

- **Unknown command name** (Decision 7): `command_name` is not declared in the
  device manifest → we raise **before** calling `execute`; no execution is
  created.
- **Confirmation gate refuses** (Decision 6): the command declares `confirmation`
  and `human_confirmed_this_action` is `False` → we raise **before** calling
  `execute`; no execution is created.
- **`execute` fails** (e.g. upstream 403 for insufficient role, network error) →
  the SDK raises on its own and the exception propagates to the agent. We do not
  catch it.
- **`execute` returns** → map the `Execution` to `CommandExecution` and return
  it. The `state` field communicates the outcome (`success`/`error`/`timeout`/
  `unsync`), consistent with how `search_command_executions` already returns
  items of any state — device error/timeout states are **values, not
  exceptions**. The returned `id` is the handle the agent needs to reference,
  audit, or follow up the execution.

### 4. No argument validation in v1

Arguments are passed through to the device unchecked beyond what the upstream
API enforces. The agent discovers argument names/types via
`read_blueprint(section="commands")`; the device validates authoritatively.
Local validation, numeric bounds, and `default`/`sensitive` handling are
deferred. Command-*name* existence is checked against the manifest — that is a
structural check, not argument validation (see Decision 7).

### 5. RBAC unchanged; defense in depth

Access control is not re-implemented. The upstream API enforces
`authorized_role >= command.access_level` and returns 403 on insufficient
privilege, which the SDK raises and which propagates to the agent (Decision 3);
the MCP server never bypasses or pre-authorizes. The tool is registered with
`readOnlyHint=False`, `destructiveHint=True` as an additional advisory signal to
clients.

### 6. Server-enforced confirmation via `human_confirmed_this_action`

Blueprint manifests may declare a per-command `confirmation` block
(`severity`/`title`/`description`) for commands the vendor considers
consequential. We expose this and enforce a server-side gate:

- `execute_command` takes `human_confirmed_this_action: bool` (default `False`).
- The server fetches the manifest and resolves the command declaration **itself**
  (it does not trust the agent's representation of whether confirmation is
  required). If the resolved command declares `confirmation` **and**
  `human_confirmed_this_action` is `False`, the tool **raises before `execute`**
  — no execution is created. The error message includes the `confirmation`'s
  `title`/`description` so the agent knows what to ask.
- For commands without a `confirmation` block, the flag is ignored (the default
  `False` is fine).

The parameter uses **`human`, not `user`**, deliberately. In auth contexts
"user" is the authenticated principal, which an LLM can map onto *itself* (it
holds the token, it is the API caller). `human` forces the disambiguation: a
flesh-and-blood person must have confirmed. The name is the social-engineering
lever — well-behaved agents read the attestation, ask the human via their native
conversational ability (presenting the `title`/`description`), and only then set
the flag. The `CommandDeclaration` and `execute_command` docstrings spell this
out: check the declaration via `read_blueprint`; for a confirmation-declared
command, obtain a human's approval before setting `human_confirmed_this_action` —
the name reads as a claim the caller is making, which is the friction we want.

This is an **enforced assertion, not a guarantee.** The server verifies the flag
was set for confirmation-declared commands; it cannot verify that a human
actually confirmed. An ill-behaved agent can set the flag without asking, and
nothing in v1 prevents that. A server-enforced `ctx.elicit` round-trip — which
actually reaches a human through the client — is the planned follow-up (Decision
7) to close that gap; elicitation is deferred because client support for it is
currently poor.

`confirmation` is captured on `CommandDeclaration` (domain and MCP), mapped by
`EnapterDataMapper` from the manifest when present (otherwise `None`), and
surfaced via `read_blueprint(section="commands")`.

### 7. Command-name existence check (not argument validation)

The server resolves the command declaration from the device manifest itself
(the same fetch the confirmation gate uses — Decision 6). If the resolved
`command_name` is not declared in the manifest, the tool raises **before**
calling `execute` — no execution is created — and the error message names the
available commands so the agent can recover (correct a typo or hallucination).

This is a structural check against the device's own blueprint, not a permission
check: it does not duplicate or drift from upstream RBAC (Decision 5), and it is
distinct from the *argument* validation (`min`/`max`, type/enum/required) that
Decision 4 explicitly defers. The manifest is authoritative for which commands a
device exposes, so failing fast locally is safe and avoids a wasted round-trip.
A command present in the manifest without a `confirmation` block still proceeds
at the default `human_confirmed_this_action=False` (Decision 6).

### 8. Deferred to a follow-up spec

The following are intentionally **out of scope for this spec**:

- **Server-enforced `ctx.elicit`** as a real human round-trip on commands that
  declare `confirmation` — closes the "agent can lie" gap left by the
  `human_confirmed_this_action` flag (Decision 6). Deferred due to poor current
  client support for elicitation.
- **An async execution model** (`create_execution` + poll), **progress logging**,
  and/or **a separate wait tool** (or `wait` argument) to stream progress and
  handle long commands without a single blocking call — deferred until production
  usage shows it is needed.
- **Local argument validation** (`min`/`max`, type/enum/required checks).

The v1 defenses are therefore: the opt-in kill switch, upstream RBAC,
`destructiveHint=True`, the `human_confirmed_this_action` gate plus docstring
guidance, and the execution audit trail (recoverable via
`search_command_executions`).

## Constraints

- Do **not** change the semantics or annotations of the existing seven tools;
  they remain read-only (`readOnlyHint=True`).
- Do **not** change the default behavior of the server: command execution stays
  OFF unless explicitly enabled.
- Do **not** bypass, weaken, or re-implement upstream RBAC. The SDK's 403
  propagates; do not pre-check permissions in a way that could drift from the
  server.
- Do **not** implement server-side elicitation or validate arguments in this
  spec (both deferred — see Decision 8). In particular, do not add `min`/`max` to
  command argument declarations. (Capturing and exposing the `confirmation` block
  and the `human_confirmed_this_action` gate **are** in scope — see Decision 6.)
- Do **not** add rate limiting (deferred).
- Do **not** add a `wait`/`timeout` argument, a second execution tool, a `ctx`
  parameter, or progress logging to `execute_command`. It is one blocking tool
  that uses `commands.execute` directly (not `create_execution` + polling). These
  are deferred per Decision 8.
- Do **not** catch the SDK's exceptions for `execute` (e.g. 403, network); let
  them propagate.
- The confirmation parameter is named exactly `human_confirmed_this_action` (the
  `human` framing is intentional — see Decision 6).
- The wire format of existing models is unchanged except for the additive,
  optional `confirmation` field on command declarations.

## Acceptance Criteria

1. **Kill switch (off).** With `command_execution_enabled` falsy (the default),
   `tools/list` returns exactly the seven existing tools and does not include
   `execute_command`.

2. **Kill switch (on).** With `command_execution_enabled` truthy, `tools/list`
   returns eight tools including `execute_command`.

3. **CLI/config wiring.** `--command-execution-enabled` (choices `0`/`1`,
   default from `ENAPTER_COMMAND_EXECUTION_ENABLED`, default `"0"`) sets
   `ServerConfig.command_execution_enabled`, which controls criteria 1 and 2.

4. **Tool annotations.** `execute_command` is registered with
   `readOnlyHint=False`, `destructiveHint=True`, and a non-empty `title`. The
   seven existing tools remain `readOnlyHint=True`.

5. **Tool input schema.** `execute_command` accepts `device_id: str` (required),
   `command_name: str` (required), `arguments: object | null` (optional,
   `default: null`; `null`/omitted means no arguments — the upstream SDK
   normalizes `null` to `{}`), and `human_confirmed_this_action: bool`
   (default `False`) — and no other parameters.
   `tests/integration/schemas/execute_command.json` is committed and asserts this
   shape and the exact parameter name.

6. **`confirmation` enrichment.** `domain.CommandDeclaration` has an optional
   `confirmation` capturing `severity`, `title`, and `description`. The MCP-layer
   `CommandDeclaration` mirrors it. `EnapterDataMapper` maps it from the manifest
   when present and leaves it `None` when absent.

7. **`confirmation` exposed.** `tests/integration/schemas/read_blueprint.json` is
   regenerated and shows `confirmation` on command declarations.

8. **Confirmation gate.** For a command whose manifest declaration includes a
   `confirmation` block, `execute_command` with `human_confirmed_this_action=False`
   raises **before** calling `execute` and the message includes the block's
   `title`/`description`; with `human_confirmed_this_action=True` it proceeds. For
   a command without a `confirmation` block, the flag is ignored and execution
   proceeds at the default `False`. The server resolves the declaration from the
   manifest itself. (Verifiable with a mock API: `execute` is **not** called on
   refusal, and **is** called otherwise.)

9. **Confirmation docstrings.** The `CommandDeclaration` model docstring and the
   `execute_command` tool docstring direct the agent to obtain a **human's**
   approval (presenting the `title`/`description`) before executing a command
   whose `confirmation` is present, and to set `human_confirmed_this_action=True`
   to attest it. Both docstrings appear in their committed schema snapshots.

10. **Execution.** Once the gate passes, `core` calls
    `commands.execute(device_id, command_name, arguments)`, which blocks until the
    command completes or the upstream timeout fires, then maps the returned
    `Execution` to `CommandExecution` and returns it. There is no poll loop and no
    logging.

11. **Return on completion.** When `execute` returns, the tool returns the full
    MCP `CommandExecution` (including `id`, `state`, and `response_payload`). The
    `state` field communicates the outcome for every terminal state, including
    `error`/`timeout`/`unsync` (the tool does **not** raise for these — it returns
    the `CommandExecution` with that state).

12. **SDK errors propagate.** If `commands.execute` raises (e.g. upstream 403,
    network error), the exception propagates to the agent unmodified (the tool
    does not catch it).

13. **Recovery after cancellation.** If the tool call is cancelled or times out
    before returning, the agent can recover the outcome via
    `search_command_executions` by `device_id`/time (an execution record is
    created by `execute`; the agent has no `id` in this case).

14. **RBAC surfacing.** An upstream authorization failure (403) reaches the agent
    via the propagated SDK exception (criterion 12); the server does not pre-check
    or bypass it.

15. **Tests.** Unit tests cover: the unknown-command-name gate — a name not in
    the manifest → raises and `execute` is not called; the confirmation gate —
    confirmation-declared + flag `False` → raises and `execute` is not called;
    confirmation-declared + flag `True` → proceeds; a command present in the
    manifest without `confirmation` + flag `False` → proceeds; `execute`
    returning a success `Execution` (returns a `CommandExecution` with
    `response_payload`); `execute` returning an `error`/`timeout`/`unsync`
    `Execution` (returns a `CommandExecution` with that state); and an `execute`
    SDK raise propagating. Plus `EnapterDataMapper` mapping `confirmation`
    (present → value, absent → `None`). The integration test still asserts exactly
    seven tools under the default (disabled) config, and an enabled-config case
    asserts eight tools and the `execute_command` schema snapshot.

16. **Unknown command name.** For a `command_name` not present in the device
    manifest, `execute_command` raises **before** calling `execute` (no execution
    is created) and the message names the available commands. (Verifiable with a
    mock API: `execute` is not called.)

17. **README.** `README.md` is updated: the `execute_command` tool is added to
    the "Available Tools" table (noting it is disabled by default and enabled via
    `--command-execution-enabled` / `ENAPTER_COMMAND_EXECUTION_ENABLED`), and a
    usage example demonstrates executing a command including the
    human-confirmation flow (presenting the `confirmation` `title`/`description`
    and setting `human_confirmed_this_action=True`).

18. `make lint` and `make test` pass.
