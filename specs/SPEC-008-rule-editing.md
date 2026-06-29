# SPEC-008: Rule Editing

## Context

The MCP server currently exposes automation rules as read-only data:

- `search_rules` lists rules on a site.
- `read_rule` reads a rule's Lua script as paginated lines.

The upstream Enapter API already supports mutating rule-engine state: creating
rules, updating rule scripts, renaming rules, enabling/disabling rules, and
deleting rules. Exposing those operations directly would let an AI assistant
modify automation that can execute commands on physical energy hardware.

This spec introduces a narrow rule-editing workflow where the assistant can
create, maintain, and remove **MCP-managed rules**, while humans remain
responsible for publishing newly created automation by enabling rules outside
MCP.

The core idea is:

- `disabled` is the creation safety boundary. New MCP-managed rules are created
  disabled, so the assistant cannot publish new live automation.
- A reserved slug prefix is the authorship boundary. The assistant may mutate
  only rules whose slug is explicitly marked as MCP-managed.
- `disabled` is also the mutation safety boundary. Mutating enabled rules is
  forbidden, even when they are MCP-managed.
- The assistant never gets an enable operation. Humans enable newly created rules
  in the Enapter UI after reviewing and accepting responsibility.

## Architectural Decisions

### 1. Opt-in kill switch, default OFF

Rule editing is registered only when the server is explicitly configured to
allow it (`ServerConfig.rule_editing_enabled`, driven by
`ENAPTER_RULE_EDITING_ENABLED` / `--rule-editing-enabled`, default `"0"`).

Existing deployments remain read-only by default. This mirrors the command
execution kill switch from SPEC-007.

### 2. Three rule-editing tools

This spec adds three tools when rule editing is enabled:

- `create_rule`: create a disabled MCP-managed rule.
- `edit_rule`: apply a content-match edit to an MCP-managed rule.
- `delete_rule`: delete a disabled MCP-managed rule.

`create_rule` and `edit_rule` return the updated MCP `Rule` object (`id`,
`slug`, `enabled`, `state`, and `script_summary`). Agents can use `read_rule`
after an edit when they need to inspect the resulting source code. `delete_rule`
returns no result; agents can confirm deletion via `search_rules`.

`create_rule` accepts `site_id`, `slug`, and full `script_code`. The `slug` must
start with the reserved MCP-managed prefix. The tool always creates the upstream
rule disabled and pinned to runtime version v3. If the supplied slug already
exists, the upstream API error propagates.

`edit_rule` accepts `site_id`, `rule_id`, `old_string`, and `new_string`.

`delete_rule` accepts `site_id` and `rule_id`, both required.

### 3. MCP manages prefixed rules only

The rule-editing surface is for disabled MCP-managed rules, not for arbitrary or
live rules.

The server refuses to edit or delete a rule unless:

- the rule is currently disabled, and
- the rule slug starts with the reserved MCP-managed prefix defined by this spec.

Additionally, `edit_rule` refuses to edit a rule whose runtime version is not v3.

Guards are evaluated in a fixed order, each raising before any upstream mutating
call, so that a simultaneously-violating rule produces one deterministic error:

1. gateway online (all three tools);
2. `old_string != ""` and `old_string != new_string` (`edit_rule` only);
3. rule is disabled (`edit_rule`, `delete_rule`);
4. slug starts with `mcp-` (`edit_rule`, `delete_rule`);
5. runtime version is v3 (`edit_rule` only);
6. `old_string` appears exactly once (`edit_rule` only).

This prevents the assistant from accidentally modifying human-authored disabled
rules, and prevents assistant-made changes from affecting live automation
immediately. The prefix is an ownership/consent boundary, not a safety guarantee.
Humans may remove the prefix to opt a rule out of MCP management, or add it to a
disabled rule to opt it in.

### 4. No enable tool, no rename tool

The server does not expose an operation that enables a rule.

The human deployment flow for newly created rules is deliberately outside MCP: a
human reviews the rule and enables it in the Enapter UI. The assistant has no
tool-level path to publish new automation.

The server also does not expose a rename operation. Renaming can be performed as
`delete_rule` followed by `create_rule`, which keeps the explicit slug and the
disabled/prefixed guards intact without adding a separate mutation path.

If a human enables an MCP-managed rule and later wants the assistant to edit or
delete it, the human must disable it first, ask the assistant to mutate the
now-disabled MCP-managed rule, review the result, and re-enable the rule in the
Enapter UI if they accept responsibility. This keeps responsibility for live
automation changes with the human.

Disabling rules is deferred. This spec only establishes the MCP-managed rule
authoring, editing, and deletion workflow.

### 5. Create disabled MCP-managed rules

The server exposes a creation workflow for new MCP-managed rules. Created rules
are always disabled regardless of caller input. The assistant cannot create live
automation.

The reserved MCP-managed slug prefix is `mcp-`. The check is the byte-exact,
case-sensitive Python expression `slug.startswith("mcp-")`. No case-folding,
stripping, or Unicode normalization is applied, so `"MCP-..."`, `" mcp-..."`,
and look-alike Unicode slugs do not match. The slug `mcp-` itself (no suffix) is
permitted. `create_rule` rejects a `slug` that does not start with `mcp-`; it
does not silently prepend the prefix. The final slug is therefore explicit in the
tool call and visible in the Enapter UI.

Created rules always use runtime version v3. Runtime v3 exposes the scheduler
from the script itself, so no execution interval is configured and `create_rule`
takes no `runtime_version` or `exec_interval` parameters.

### 6. Edit by unique content match

Rule edits use a content-match workflow rather than full-script replacement from
the agent's perspective.

The assistant supplies an exact `old_string` copied from the current script and a
`new_string`. The server fetches the current script, requires `old_string` to
appear exactly once, replaces that occurrence, and writes the resulting full
script through the upstream API.

`old_string` must be non-empty. An empty `old_string` is rejected before calling
upstream update regardless of script content (an empty pattern would otherwise
match at every position).

An edit where `old_string == new_string` is rejected before calling upstream
update. This no-op check runs before the match-count check, so a no-op edit
raises the no-op error even when `old_string` is absent or ambiguous.

This model is intentionally similar to file-editing tools used by coding agents:

- no line-number drift or off-by-one errors;
- bounded token cost proportional to the edit size, not the whole script;
- a stale or hallucinated edit fails when `old_string` is absent;
- an ambiguous edit fails when `old_string` appears multiple times.

The upstream API still receives a complete script update. The safe patch
semantics are implemented by the MCP server.

Because the upstream `update_rule_script` endpoint requires a complete
`RuleScript`, edits preserve the current rule's `runtime_version` and
`exec_interval` when writing the updated code. Because `edit_rule` only accepts
v3 rules, the written `runtime_version` is always v3.

### 7. No enabled-rule mutation

Editing or deleting an enabled rule is forbidden, even if its slug starts with
`mcp-`. The server raises before calling upstream update/delete.

This intentionally forces the human workflow for live rules:

- disable the rule in the Enapter UI;
- ask the assistant to edit or delete the now-disabled MCP-managed rule;
- review the result;
- re-enable the rule in the Enapter UI if the human accepts responsibility.

### 8. No replace-all mode in v1

`old_string` must match exactly once. Replacing all occurrences is deferred until
we see whether agents actually struggle with unique-match edits.

If the same snippet appears multiple times, the assistant must include enough
surrounding context in `old_string` to make the match unique.

### 9. Return values

After a successful create or edit, the tool returns the updated MCP `Rule` object
(`id`, `slug`, `enabled`, `state`, and `script_summary`).

The script itself is not returned by the write tools. The assistant can call
`read_rule` after a create or edit when it needs to inspect or present the final
source code. Humans remain responsible for reviewing the code before enabling a
rule in the Enapter UI.

`delete_rule` returns no result. The server still fetches the rule before
deleting to enforce the disabled and prefix guards; if the rule is missing, that
fetch raises and the error propagates (agents should not delete rules that do not
exist).

### 10. Gateway availability and RBAC

Rule creation, editing, and deletion require the site's gateway to be online,
consistent with `search_rules` and `read_rule`.

The MCP server does not reimplement upstream RBAC. Authorization failures from
the upstream API propagate to the agent.

### 11. Deferred operations

Full rule lifecycle management beyond create/edit/delete is intentionally out of
scope for this spec.

Deferred operations:

- `enable_rule`: intentionally not exposed by this workflow; reconsider only with
  a separate safety design.
- `disable_rule`: may be useful because it reduces risk, but it is still an
  operational change and needs its own spec.
- replace-all or multi-hunk transactional edits: deferred.

### 12. Concurrency and the fetch-then-write window

The guards (disabled, `mcp-` prefix, v3) are evaluated against the rule state
fetched immediately before the mutating upstream call. The upstream API offers no
atomic check-and-write today (no ETags / conditional update), so a concurrent
mutation between the guard fetch and the write is not prevented: in that window a
human could enable the rule, or rename it to add or remove the `mcp-` prefix.

This is accepted in v1. The threat this spec defends against is a misbehaving
agent breaking production automation, not a human racing the assistant — a human
acting concurrently is exercising their own authority, and the guards block the
agent's non-adversarial mistakes. The implementation must leave a code comment at
the fetch-then-write site documenting this window, so that when the platform
gains conditional updates (ETags) the gap can be closed deliberately.

## Constraints

- Do not register rule-editing tools unless `rule_editing_enabled` is true.
- Do not expose an enable-rule operation.
- Do not expose a rename operation.
- Do not edit or delete enabled rules.
- Do not edit or delete rules whose slug lacks the MCP-managed prefix.
- Do not edit rules whose runtime version is not v3.
- Do not allow content-match edits with an empty `old_string`.
- Do not allow content-match edits that match zero or multiple occurrences.
- Do not change the behavior or schemas of existing read-only tools.
- Do not reimplement upstream RBAC.

## Acceptance Criteria

1. **All optional tools disabled.** With `rule_editing_enabled` falsy and
   `command_execution_enabled` falsy, `tools/list` returns exactly the seven
   read-only tools and does not include `create_rule`, `edit_rule`,
   `delete_rule`, or `execute_command`.

2. **All optional tools enabled.** With both `rule_editing_enabled` and
   `command_execution_enabled` truthy, `tools/list` returns exactly eleven tools:
   the seven read-only tools plus `execute_command`, `create_rule`, `edit_rule`,
   and `delete_rule`.

3. **CLI/config wiring.** `--rule-editing-enabled` (choices `0`/`1`, default from
   `ENAPTER_RULE_EDITING_ENABLED`, default `"0"`) sets
   `ServerConfig.rule_editing_enabled`.

4. **Tool annotations.** Rule-editing tools are registered with
   `readOnlyHint=False`, `destructiveHint=True`, and the titles `Create Rule`,
   `Edit Rule`, and `Delete Rule` respectively. Existing read-only tools remain
   `readOnlyHint=True`.

5. **Tool input schemas.** `create_rule` accepts exactly `site_id`, `slug`, and
   `script_code`, all required. `edit_rule` accepts exactly `site_id`, `rule_id`,
   `old_string`, and `new_string`, all required. `delete_rule` accepts exactly
   `site_id` and `rule_id`, both required.

6. **Create disabled v3 rule.** Creating an MCP-managed rule always calls upstream
   create with the rule disabled and runtime version v3, and returns the created
   `Rule`.

7. **Prefix contract.** The MCP-managed slug prefix is exactly `mcp-`, checked
   byte-exact and case-sensitively via `slug.startswith("mcp-")` (no
   normalization), and is used by create, edit, and delete flows.

8. **Reject unprefixed create.** Creating a rule whose `slug` does not start with
   `mcp-` raises before calling upstream create.

9. **No enable or rename path.** No MCP tool added by this spec can enable or
   rename a rule.

10. **Mutate disabled MCP-managed rule.** Editing and deleting succeed only when
    the target rule is disabled and its slug starts with `mcp-`.

11. **Reject enabled rule mutation.** Editing or deleting an enabled rule raises
    before calling upstream, even if its slug starts with `mcp-`.

12. **Reject unprefixed disabled rule mutation.** Editing or deleting a disabled
    rule whose slug does not start with `mcp-` raises before calling upstream.

13. **Reject non-v3 edit.** Editing a disabled MCP-managed rule whose runtime
    version is not v3 raises before calling upstream update. Delete is not
    restricted by runtime version.

14. **Reject no-op edit.** Editing with `old_string == new_string` raises before
    calling upstream update, and this check runs before the match-count checks.

15. **Reject empty old_string.** Editing with `old_string == ""` raises before
    calling upstream update.

16. **Unique match.** Editing with a non-empty `old_string` that appears exactly
    once replaces only that occurrence and calls upstream update with the full
    updated script.

17. **No match.** Editing with an `old_string` that is absent raises before
    calling upstream update.

18. **Ambiguous match.** Editing with an `old_string` that appears more than once
    raises before calling upstream update and tells the assistant to include more
    surrounding context.

19. **Metadata preserved on edit.** Content-match edits call upstream
    `update_rule_script` with runtime version v3 and the current rule's
    `exec_interval`. For v3 rules `exec_interval` is `None`, so in practice this
    preserves `None`; it is passed through unchanged to avoid assuming the
    upstream representation.

20. **Delete calls upstream.** Deleting a disabled MCP-managed rule calls
    upstream delete, returns no result, and the rule is absent from subsequent
    `search_rules`.

21. **Delete missing rule raises.** Deleting a `rule_id` that does not exist at
    the site raises (the pre-delete guard fetch surfaces the upstream 404) and
    does not call upstream delete.

22. **Gateway required.** Create, edit, and delete operations check gateway
    availability consistently with `search_rules` and `read_rule`.

23. **SDK errors propagate.** Upstream authorization and network errors,
    including a missing-rule 404, propagate unmodified unless the server rejected
    the operation before submission for a guard violation.

24. **Updated rule returned.** Successful create/edit responses return the updated
    MCP `Rule` object.

25. **Schema snapshots.** `tests/integration/schemas/create_rule.json`,
    `edit_rule.json`, and `delete_rule.json` are committed and assert — per tool —
    the exact required-parameter set named in criterion 5 and the
    `readOnlyHint=False` / `destructiveHint=True` annotations with the titles
    from criterion 4.

26. **README.** `README.md` adds the three tools to the *Available Tools* table
    (marked Read-write / Disabled by default) and documents the MCP-managed rule
    workflow, the `mcp-` slug prefix, the fact that newly created rules are
    disabled, the fact that enabling is not exposed, the fact that mutating
    enabled rules is forbidden, and the kill switch.

27. **TOCTOU documented.** The fetch-then-write code path in `ApplicationServer`
    carries a comment noting the lack of an upstream conditional-update primitive
    and the accepted race window (see Decision 12).

28. `make lint` and `make test` pass.
