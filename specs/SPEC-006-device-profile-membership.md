# SPEC-006: Device Profile Membership

## Context

The Enapter rule engine exposes `device.implements()` as a first-class Lua API,
returning the list of profiles a device implements. Rule code branches on
profile membership:

```lua
local implements, _ = device.implements()
if implements["energy.battery"] then
  local soc = device.telemetry.now("battery_soc")
  ...
end
```

An agent deciphering such a rule needs to resolve which profiles the target
device implements. Profile membership is a composite fact — a profile like
`energy.battery` requires multiple declarations (soc, electrical, status, etc.)
spread across the manifest. This membership is recorded only in the manifest's
top-level `implements` field; it cannot be reconstructed from per-declaration
mappings alone.

Without exposing this list, the agent cannot answer "does this device implement
`energy.battery`?" from server data. The profiles repository at
`https://github.com/Enapter/profiles` documents what each profile means, but
the server must expose which profiles a device claims to implement.

## Architectural Decisions

1. **Add `implements: list[str]` to `domain.DeviceManifest`.** Each entry is a
   dot-notation profile identifier string (e.g., `energy.battery`). Mapped from
   the manifest dict's `implements` key, defaulting to `[]` when absent.

2. **Add `BlueprintSection.IMPLEMENTS = "implements"`,** mirroring the YAML key
   (consistent with `TELEMETRY`, `PROPERTIES`, `ALERTS`, `COMMANDS`).

3. **`read_blueprint(section="implements")` returns `list[str]`** — the
   device's implemented profile names from `manifest.implements`, filtered by
   `name_regexp` (matched against the profile name string), paginated by
   `offset`/`limit`. The return-type union of `read_blueprint` grows by a `str`
   variant. The agent knows from its `section` input what item type to expect,
   so the heterogeneous union is not ambiguous in practice.

4. **Add the profiles-repo link to the `read_blueprint` docstring.** This is
   where the agent encounters profile data — per-declaration `implements`
   mappings on declarations (SPEC-005) and the full list via the `implements`
   section. The link gives the external reference for resolving profile names
   against the canonical definitions at
   `https://github.com/Enapter/profiles`.

5. **The section is additive.** Existing sections (telemetry, properties,
   alerts, commands) and their return types are unchanged. An agent only calls
   `section="implements"` when deciphering `device.implements()` in rule code.

## Constraints

- Do not add `implements` as a field on `domain.Device`, `mcp.models.Device`,
  or `BlueprintSummary`. Profile membership is not part of search results — it
  surfaces only when the agent explicitly reads the `implements` section.
- Do not add an `implements` filter to `search_devices`. Profile-name-based
  device search is out of scope.
- Do not add a `search_profiles` tool or `Profile` domain/MCP model.
- Do not change existing `read_blueprint` sections or their return types. The
  new `IMPLEMENTS` section is additive.
- Do not add PyYAML or any YAML-parsing dependency.

## Acceptance Criteria

1. `domain.DeviceManifest` has `implements: list[str]` (required).

2. `EnapterDataMapper.to_device_manifest` maps `implements` from the manifest
   dict's `implements` key, defaulting to `[]` when absent.

3. `domain.BlueprintSection` has `IMPLEMENTS = "implements"`.

4. `ApplicationServer.read_blueprint` with `section=IMPLEMENTS` returns
   `list[str]` from `manifest.implements`, filtered by `name_regexp`
   (matched against the profile name string) and paginated by `offset`/`limit`.

5. The `read_blueprint` return-type union (both `core.ApplicationServer` and
   `mcp.server.Server` layers) includes `str`.

6. The `read_blueprint` tool docstring:
   - Lists `"implements"` among the available sections.
   - References `https://github.com/Enapter/profiles` and explains that it
     documents the standardized profiles that blueprints implement.

7. The `tests/integration/schemas/read_blueprint.json` snapshot is regenerated
   and shows:
   - `"implements"` in the `section` input enum.
   - `string` as an `anyOf` variant in the output item schema.

8. Unit tests cover:
   - `to_device_manifest` maps `implements` (present → list; absent → `[]`).
   - `ApplicationServer.read_blueprint` with `section=IMPLEMENTS` returns the
     filtered, paginated profile name list (mocked manifest).
   - The MCP-layer `read_blueprint` returns bare strings for the `IMPLEMENTS`
     section and declarations for the other sections.

9. `make check` passes.
