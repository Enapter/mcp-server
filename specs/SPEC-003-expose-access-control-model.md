# SPEC-003: Expose Access Control Model to MCP Clients

## Context

SPEC-001 introduced `authorized_role` on `Site` and `Device`; SPEC-002 introduced `access_level` on blueprint declarations. Both fields are exposed to MCP clients as JSON schema enum strings, but the schemas carry no description of what the values mean or how to compare them.

This is a problem because MCP clients are AI agents. They learn about the API solely from the JSON schema and tool descriptions surfaced by MCP's `list_tools` — they do not read external documentation. A client inspecting `Site.authorized_role: "readonly"` today has no way to know what that means, and a client looking at `PropertyDeclaration.access_level: "user"` has no model for combining the two to decide whether the property is visible.

The Enapter access control model is:

- The six role values form a **total order by priority**, lowest to highest: `readonly`, `user`, `owner`, `installer`, `vendor`, `system`.
- Each higher-priority role includes all permissions of every lower-priority role.
- For declaration-level access (properties, telemetry attributes, commands), the comparison is per-declaration: a user can read the value (or execute the command) only if their `authorized_role` is at or after the declaration's `access_level` in the priority order.
- `system` is reserved/internal and is not granted to typical users.
- Manifest defaults when `access_level` is unset: properties and telemetry attributes → `readonly`; commands → `user`.

## Architectural Decisions

1. **Document the model in the response item docstrings**, not in the `search_sites` / `search_devices` tool docstrings. A client inspecting a returned `Site` or `Device` sees the model docstring as the `description` of the item schema; the access model is therefore visible at the point of inspection. Repeating it in the tool docstring is redundant and would inflate the surface shown on every `list_tools` call.

2. **Do not add an access model paragraph to the `read_blueprint` tool docstring.** The access model is already explained in the declaration model docstrings (PropertyDeclaration, TelemetryAttributeDeclaration, CommandDeclaration), which are the items returned by this tool. Adding it to the tool docstring would be redundant.

3. **Attach a minimal description to the `AccessRole` type.** The type is wrapped in `Annotated[Literal[...], Field(description=...)]` with a short description that states the priority order: "Roles in priority order: readonly < user < owner < installer < vendor < system." This propagates to every `authorized_role` and `access_level` field, giving clients the ordering they need to perform comparisons. The description is minimal (one line) to avoid wasting context; the full access model (comparison rule, defaults) is explained in the model docstrings.

4. **Add an access control note to the `get_historical_telemetry` tool docstring**, not to the `HistoricalTelemetry` model docstring. The note ("Telemetry attributes the user cannot read are absent from the result") is a behavioral observation about the tool's output, not a property of the data model. The `HistoricalTelemetry` docstring remains minimal.

### Priority order

The roles, lowest to highest: `readonly`, `user`, `owner`, `installer`, `vendor`, `system`. A user can read a property value, telemetry data, or execute a command when their `authorized_role` is at or after the declaration's `access_level` in this order.

## Constraints

- Do not change the wire format, or `domain.AccessRole`. The `mcp.AccessRole` type is wrapped in `Annotated[Literal[...], Field(description=...)]` to attach the priority order; the underlying literal values and their order are fixed.
- Do not add new tools, parameters, or filters.
- Do not add `access_level` to `AlertDeclaration` or `CommandArgumentDeclaration`.
- Do not add a `docs/access-roles.md` (or any human-facing documentation file) in this spec. AI clients do not read such files; the schemas are the only surface that matters. A human-facing doc, if needed, is a separate spec.
- Do not modify the `search_sites` or `search_devices` tool docstrings. The `get_historical_telemetry` tool docstring may be updated to add the access control note.

## Acceptance Criteria

1. `Site`, `Device`, `PropertyDeclaration`, `TelemetryAttributeDeclaration`, and `CommandDeclaration` each have a non-empty class docstring that appears as `description` in their generated JSON schema and explains the access model.

2. The `HistoricalTelemetry` docstring is minimal (no access control note). The access control note appears in the `get_historical_telemetry` tool docstring instead.

3. Each `authorized_role` and `access_level` field has a `description` in the generated JSON schema that states the priority order: "Roles in priority order: readonly < user < owner < installer < vendor < system."

4. The `read_blueprint` tool docstring does not include an access model paragraph (the model is explained in the declaration model docstrings).

5. The `get_historical_telemetry` tool docstring includes the access control note: "Telemetry attributes the user cannot read (per their `authorized_role`) are absent from the result."

6. The tool docstrings for `search_sites` and `search_devices` are unchanged.

7. The wire format and the `domain.AccessRole` enum are unchanged.

8. The integration schema snapshots for `search_sites`, `search_devices`, `read_blueprint`, and `get_historical_telemetry` are regenerated and committed. The schema snapshots are the sole enforcement of the description requirements in criteria 1 and 5 — a future change that drops or rewrites a description is caught by the snapshot diff in code review.

9. `make lint` and `make test` pass.
