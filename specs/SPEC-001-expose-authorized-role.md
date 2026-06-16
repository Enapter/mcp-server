# SPEC-001: Expose Site and Device Authorization Roles to MCP Clients

## Context

The Enapter Python SDK `0.24.*` exposes an `authorized_role` field on the HTTP
API models for `Site` and `Device`, surfacing the authenticated user's access
level on each resource:

- `READONLY`
- `USER`
- `OWNER`
- `INSTALLER`
- `SYSTEM`
- `VENDOR`

Currently the MCP server drops this field while mapping SDK responses through
`core.SiteDTO` / `core.DeviceDTO` → `domain.Site` / `domain.Device` →
`mcp.models.Site` / `mcp.models.Device`. As a result, MCP clients have no way
to know whether the user is a read-only viewer or an administrator for a given
site or device.

Exposing the role lets AI assistants and other clients reason about permission
boundaries (for example, warning that a user lacks rights to modify a device)
and aligns the MCP output with the underlying Enapter HTTP API.

## Architectural Decisions

1. **Surface the role in existing tool responses.** `authorized_role` is an
   attribute of `Site` and `Device` resources, so it naturally belongs in the
   response payloads of `search_sites` and `search_devices`. No new tools are
   introduced.

2. **No filtering for now.** The Enapter HTTP API does not support filtering
   sites or devices by `authorized_role`. Adding client-side filtering would
   complicate the search tools without meaningful performance benefit while the
   MCP server remains read-only. Filtering can be reconsidered later if a
   concrete use case emerges.

3. **Lowercase string values in MCP models.** The SDK and API docs use
   uppercase role names (`"OWNER"`), but the MCP server already exposes enum
   values as lowercase strings (e.g. `"native"`, `"online"`). Using lowercase
   (`"owner"`, `"installer"`, etc.) preserves internal consistency. The domain
   layer will use an `AccessRole` enum with lowercase values, and the MCP
   layer will expose it as a matching `Literal` type.

4. **Use `AccessRole` as the type name.** The SDK `0.24.*` renames the role
   type from `AuthorizedRole` to `AccessRole`. The MCP server uses its own
   `domain.AccessRole` enum with lowercase values and maps to/from the SDK
   type.

5. **Two-layer mapping is preserved.** The SDK value flows through
   `EnapterAPI` → `EnapterDataMapper` → `ApplicationServer` → domain model →
   MCP model, just like `connectivity_status` or `type`.

6. **Per-blueprint access levels are out of scope.** Blueprint manifest entries
   may also contain `access_level` metadata for properties, telemetry,
   commands, and configuration groups. That work is deliberately deferred to a
   separate follow-up task.

## Requirements

1. The MCP server must expose `authorized_role` for every site returned by
   `search_sites`.

2. The MCP server must expose `authorized_role` for every device returned by
   `search_devices`.

3. The role values exposed to MCP clients must be lowercase strings:
   `"readonly"`, `"user"`, `"owner"`, `"installer"`, `"system"`, `"vendor"`.

4. The role must be carried through all internal layers:
   - `core.SiteDTO` and `core.DeviceDTO`
   - `domain.Site` and `domain.Device`
   - `mcp.models.Site` and `mcp.models.Device`

5. The `setup.py` dependency on `enapter` must be upgraded to `0.24.*`.

6. The existing `EnapterDataMapper.to_device_dto` must map the SDK device's
   `authorized_role` into the DTO.

7. The existing `EnapterAPI.list_sites` must map the SDK site's
   `authorized_role` into `SiteDTO`.

8. The existing `ApplicationServer` must pass the role from DTOs into domain
   models when constructing `domain.Site` and `domain.Device`.

9. The MCP `Site` and `Device` models must expose `authorized_role` as a
   required string field in their JSON schemas.

10. Unit tests and integration schema snapshots must be updated to cover the
    new field.

## Constraints

- Do not add new tools.
- Do not add `authorized_role` filter parameters to `search_sites` or
  `search_devices`.
- Do not expose per-declaration blueprint `access_level` in this task.
- Do not change the authentication or OAuth proxy behavior.
- Existing required fields on `Site` and `Device` must remain required.

## Acceptance Criteria

1. `search_sites` response items include `authorized_role` with a valid
   lowercase role string.

2. `search_devices` response items include `authorized_role` with a valid
   lowercase role string.

3. Unit tests for `Site`, `Device`, `EnapterDataMapper`, `ApplicationServer`,
   and `EnapterAPI` assert the role is propagated correctly.

4. Integration schema snapshots for `search_sites` and `search_devices` are
   regenerated and committed, showing `authorized_role` as a required string
   field.

5. `make lint` and `make test` pass.
