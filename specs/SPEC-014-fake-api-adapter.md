# SPEC-014: fake.EnapterAPI

## Context

`filesystem.EnapterAPI` (SPEC-011) is a file-backed substitute for
`http.EnapterAPI`, used only in tests. It cannot serve command-execution
scenarios. State (sites, devices, rules) is declarable as YAML, but command
*execution* is behavior — what happens when `execute_command` is called,
possibly depending on arguments, call order, or prior state. A file format
cannot express this without becoming a hand-rolled DSL ("YAML-programming"),
which is rejected. The only way to make `execute_command` do anything today is
to hard-code a result in the adapter, which turns a generic adapter into a test
mock.

This spec introduces `fake.EnapterAPI`: a programmable fake whose behavior is
ordinary Python and whose data lives in tests, never in the package. It
coexists with `filesystem.EnapterAPI` until SPEC-015 rewires the CLI to `fake://`
and deletes the filetree adapter.

`fake.EnapterAPI` implements the `core.EnapterAPI` Protocol and constructs
domain objects directly — no YAML, no pydantic mirror models, no duplication of
`http.EnapterDataMapper`.

## Architectural Decisions

### 1. fake.EnapterAPI — State + Policy + dispatcher

A new top-level package `fake/` containing machinery only — no scenario data:

```
src/enapter_mcp_server/fake/
  state.py            ← State: mutable bag of domain objects
  policy.py           ← Policy Protocol + DefaultPolicy
  enapter_api.py      ← EnapterAPI dispatcher + from_url
```

`EnapterAPI` holds a `State` and a `Policy` and implements `core.EnapterAPI`
by delegating every method to the policy, passing `state` as the first
argument:

```python
class EnapterAPI:
    def __init__(self, state: State, policy: Policy) -> None:
        self.state = state
        self.policy = policy

    async def execute_command(self, auth, device_id, command_name, arguments):
        return await self.policy.execute_command(
            self.state, auth, device_id, command_name, arguments
        )
    # ...one delegating line per core.EnapterAPI method...
```

This is the only `EnapterAPI` class in the package. There is one instance per
scenario, not N subclasses.

### 2. State is data; Policy is behavior; they are orthogonal

- **`State`** (`fake/state.py`) is a mutable container of domain objects —
  `sites`, `devices`, `rule_engines`, `rules`, `command_executions`. Pure data.
  No behavior beyond accessors.
- **`Policy`** (`fake/policy.py`) is a `Protocol` mirroring `core.EnapterAPI`'s
  methods with `state` prepended. It defines behavior only — no data. One
  exception: `core.EnapterAPI.list_command_executions` already has a parameter
  named `state: CommandExecutionState`, which collides with the prepended
  `state: State`. In the Policy that filter parameter is renamed to
  `execution_state`; the dispatcher keeps core's exact signature (`state=`) and
  forwards it positionally, so the clash is confined to the Policy surface.

A scenario selects a `State` (the world) and a `Policy` (the rules of that
world). The two are independent and composable: the same state backs multiple
policies; a policy spans states.

### 3. DefaultPolicy implements reads only; read-write raises NotImplementedError

`DefaultPolicy` (concrete, implements the full `Policy` Protocol) provides the
purely deterministic **read** methods:

- `list_sites`, `list_devices`, `get_rule`, `get_rule_engine`,
  `list_command_executions` read from `State`. `list_devices` honors an optional
  `site_id` filter; `get_rule` matches by id or slug.
- `list_rules` yields every rule in `state.rules`. `domain.Rule` carries no
  `site_id`, so the fake cannot filter per-site the way the real API does; a
  scenario's `State` is expected to contain only the relevant rules. The
  `site_id` argument is accepted for signature compatibility but not used to
  filter.
- `get_device` matches by `id` only — `domain.Device` has no `slug` field
  (unlike the filesystem pydantic model). Missing reads raise the corresponding
  core error (`DeviceNotFound`, `RuleEngineNotFound`, `RuleNotFound`), matching
  the filesystem adapter.
- `get_latest_telemetry` / `get_historical_telemetry` return empty results.

Every **read-write** method — `create_rule`, `update_rule_script`,
`delete_rule`, `execute_command` — raises `NotImplementedError`. No default
mutating or behavioral logic lives in the package. A scenario that needs a
read-write operation provides a `Policy` override implementing it (in tests,
per SPEC-016). This is the point of the split: the package contains no
hard-coded results and no "sensible" mutation defaults — only the read path,
which is deterministic and consequence-free.

`DefaultPolicy` is the base that scenario policies subclass, overriding only
the methods that diverge.

### 4. Data lives in tests, never in fake/

`fake/` contains zero scenario data. Per-scenario `State` (data) and `Policy`
overrides (behavior) are defined outside the package — under `tests/agent/` per
SPEC-016. A state module exports a `state()` factory returning a fresh `State`;
a policy module exports a `Policy` class subclassing `DefaultPolicy`.

### 5. URL: fake:// with state and policy as module paths

The fake is selected via a `fake://` URL whose query string carries the state
and policy as full dotted Python module paths:

```
fake://?state=tests.agent.states.arrakis_reboot
fake://?policy=tests.agent.policies.reboot_after_approval&state=tests.agent.states.arrakis_reboot
```

Parsed with stdlib — `urllib.parse.urlparse` + `parse_qs`:

```python
@classmethod
def from_url(cls, url: str) -> Self:
    q = parse_qs(urlparse(url).query)
    state = importlib.import_module(q["state"][0]).state()
    policy = DefaultPolicy()
    if "policy" in q:
        policy = getattr(importlib.import_module(q["policy"][0]), "Policy")()
    return cls(state=state, policy=policy)
```

- `state` is **required** — there is no universal default dataset.
- `policy` is **optional**; omitted → `DefaultPolicy`.

The URL is fully self-contained: no `--fake-root` flag, no configured package,
no default that points at `tests`. `src` never references `tests`.

### 6. Loading via importlib

`from_url` resolves module paths via `importlib.import_module`. This imports
already-installed modules on the Python path — it does not load arbitrary files
from a directory. The only code that executes is reviewed package/repo code,
the same trust level as the rest of the codebase. It is deliberately not a
self-registering registry and not a directory scan: the URL names exactly two
modules and `from_url` imports those two by full path.

### 7. Fresh state per from_url

`state()` is a factory; each `from_url` call builds a new `State`. Mutation
never leaks across scenarios.

## Constraints

- `fake/` contains no scenario data — only `State`, `Policy`, `DefaultPolicy`,
  and the `EnapterAPI` dispatcher.
- No behavior in the `EnapterAPI` dispatcher — it only delegates.
- `DefaultPolicy` implements read methods only; every read-write method raises
  `NotImplementedError`. No hard-coded results, no default mutation logic.
- `src` never imports or references `tests`.
- `mcp` layer never imports `fake` (existing layering rule).
- `fake://` requires `state`; `policy` is optional (defaults to `DefaultPolicy`).
- `state()` returns a fresh `State` on every `from_url` call.
- `fake.EnapterAPI` implements `core.EnapterAPI` and the async context manager
  protocol.
- No new top-level packages other than `fake`.

## Acceptance Criteria

1. **Package layout.** `fake/` contains exactly `state.py`, `policy.py`,
   `enapter_api.py`. No scenario data.

2. **Dispatcher delegates.** Every `core.EnapterAPI` method on
   `fake.EnapterAPI` delegates to `self.policy.<method>(self.state, ...)`. The
   dispatcher contains no logic of its own.

3. **DefaultPolicy reads.** `DefaultPolicy` implements every read method,
   returning data from the supplied `State` (telemetry methods return empty).

4. **DefaultPolicy read-write raises.** `DefaultPolicy.create_rule`,
   `update_rule_script`, `delete_rule`, and `execute_command` raise
   `NotImplementedError`.

5. **from_url — state only.**
   `fake.EnapterAPI.from_url("fake://?state=<module>")` constructs an adapter
   whose state is `<module>.state()` and whose policy is `DefaultPolicy()`.

6. **from_url — state and policy.**
   `fake.EnapterAPI.from_url("fake://?policy=<p>&state=<s>")` constructs an
   adapter whose policy is `<p>.Policy()`.

7. **Missing state raises.** `fake://?policy=<p>` (no `state`) raises.

8. **Fresh state.** Two `from_url` calls produce adapters with independent
   `State` instances; mutating one does not affect the other.

9. **Context manager.** `async with fake.EnapterAPI.from_url(url) as api:`
   works.

10. `make check` and `make test` pass.
