# SPEC-002: Expose Blueprint Declaration Access Levels

## Context

SPEC-001 exposed the authenticated user's Enapter `authorized_role` on `Site`
and `Device` resources. That tells an MCP client what permissions the user
has, but it does not tell the client whether those permissions are sufficient
to read a specific blueprint declaration.

Device blueprint declarations in Enapter manifests carry an `access_level`
attribute that defines the minimum role required to read (for properties,
telemetry, and commands) the resource. Without this information, an MCP agent
cannot know in advance whether a property, telemetry attribute, or command is
visible to the current user.

## Architectural Decisions

1. **Expose `access_level` only on declarations returned by `read_blueprint`.**
   The `read_blueprint` tool already surfaces properties, telemetry attributes,
   and commands. We add `access_level` to each of those declaration models.
   Configuration groups are out of scope for this task.

2. **Reuse the existing `AccessRole` type.** Both `access_level` and
   `authorized_role` use the same Enapter role enum values. We reuse
   `domain.AccessRole` and `mcp.models.AccessRole` instead of
   introducing a duplicate type.

3. **Apply documented defaults when `access_level` is absent.** The Enapter
   blueprint manifest docs specify:

   - Property: `readonly`
   - Telemetry attribute: `readonly`
   - Command: `user`

   When a declaration does not include `access_level`, we default to the value
   above.

4. **Keep `access_level` required in the MCP schema.** Even though the manifest
   field is optional, the MCP model always returns a value, so clients can
   rely on its presence.

5. **Alerts do not have `access_level`.** The Enapter docs do not define
   `access_level` for alerts, so `AlertDeclaration` remains unchanged.

## Requirements

1. The MCP server must expose `access_level` for every property declaration
   returned by `read_blueprint` with `section="properties"`.

2. The MCP server must expose `access_level` for every telemetry attribute
   declaration returned by `read_blueprint` with `section="telemetry"`.

3. The MCP server must expose `access_level` for every command declaration
   returned by `read_blueprint` with `section="commands"`.

4. The `access_level` values exposed to MCP clients must be lowercase strings:
   `"readonly"`, `"user"`, `"owner"`, `"installer"`, `"system"`, `"vendor"`.

5. `access_level` must use the `domain.AccessRole` enum internally
   and `mcp.models.AccessRole` in the MCP layer.

6. The `EnapterDataMapper` must apply the following defaults when
   `access_level` is missing from the manifest:
   - properties: `"readonly"`
   - telemetry attributes: `"readonly"`
   - commands: `"user"`

7. The `EnapterDataMapper` must map any explicit `access_level` value from the
   manifest by lowercasing the raw string and constructing `domain.AccessRole`.

8. The MCP `PropertyDeclaration`, `TelemetryAttributeDeclaration`, and
   `CommandDeclaration` models must expose `access_level` as a required string
   field in their JSON schemas.

9. Unit tests and the integration schema snapshot for `read_blueprint` must be
   updated to cover the new field.

## Constraints

- Do not add new tools.
- Do not expose configuration groups in this task.
- Do not change `AlertDeclaration`.
- Do not introduce a new role type; reuse `AccessRole`.

## Acceptance Criteria

1. `read_blueprint(section="properties")` response items include
   `access_level` with a valid lowercase role string.

2. `read_blueprint(section="telemetry")` response items include
   `access_level` with a valid lowercase role string.

3. `read_blueprint(section="commands")` response items include
   `access_level` with a valid lowercase role string.

4. Missing `access_level` in the manifest is replaced with the documented
   default for that declaration type.

5. Unit tests for the data mapper and declaration models assert the default
   and explicit `access_level` mapping.

6. The integration schema snapshot for `read_blueprint` is regenerated and
   committed, showing `access_level` as a required string enum on the
   declaration schemas.

7. `make lint` and `make test` pass.
