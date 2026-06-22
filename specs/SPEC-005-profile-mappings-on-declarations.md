# SPEC-005: Profile Mappings on Declarations

## Context

Enapter blueprints can alias local telemetry, property, or command names to
different profile-defined names via a per-declaration `implements` field. For
example, a blueprint may declare a telemetry attribute `irradiance` locally that
maps to `sensor.solar_irradiance.solar_irradiance` in the profile:

```yaml
telemetry:
  irradiance:
    type: float
    display_name: Solar Irradiance
    unit: W/m2
    implements: sensor.solar_irradiance.solar_irradiance
```

Automation rules access telemetry, properties, and commands by their local
blueprint names. When an agent reads rule code alongside a device's blueprint,
it needs to see the per-declaration mapping to connect local names to profile
names — especially when the two differ.

The current manifest mapper silently drops this field. This spec surfaces it as
optional metadata on existing declaration models.

## Architectural Decisions

1. **Add `implements: list[str] | None = None`** to
   `TelemetryAttributeDeclaration`, `PropertyDeclaration`, and
   `CommandDeclaration` — both domain dataclasses and MCP pydantic models. The
   field is a list of dot-notation profile identifier strings (e.g.,
   `["energy.battery"]`, `["lib.energy.battery.soc"]`). Although the blueprint
   YAML declares `implements` as a single string, the platform API serializes it
   as a single-element list. The `implements` field name conveys the meaning;
   no type alias is introduced (consistent with other list fields in the
   codebase). The platform supports per-declaration `implements` on these three
   declaration types.

2. **Do not add `implements` to `AlertDeclaration` or
   `CommandArgumentDeclaration`.** The platform does not support per-declaration
   `implements` on alerts or command arguments.

3. **Map the field from the manifest dict's per-declaration `implements` key.**
   The API delivers the value as a list. When the key is absent, the field is
   `None`. The field is purely additive metadata on existing declarations — no
   new tool, no new section, no return-type change.

## Constraints

- Do not add `implements` to `AlertDeclaration` or `CommandArgumentDeclaration`.
- Do not add a top-level `implements` field to `DeviceManifest` (separate spec).
- Do not add a new `BlueprintSection` value (separate spec).
- Do not change `read_blueprint`'s return type or existing sections.
- Do not add `implements` to the `Device` model or `BlueprintSummary`.

## Acceptance Criteria

1. `domain.TelemetryAttributeDeclaration` has `implements: list[str] | None =
   None`.

2. `domain.PropertyDeclaration` has `implements: list[str] | None = None`.

3. `domain.CommandDeclaration` has `implements: list[str] | None = None`.

4. `domain.AlertDeclaration` does NOT have an `implements` field.

5. `domain.CommandArgumentDeclaration` does NOT have an `implements` field.

6. `EnapterDataMapper` maps per-declaration `implements` from the declaration
   dict's `implements` key for telemetry attributes, properties, and commands.
   The API delivers the value as a list. When the key is absent, the field is
   `None`.

7. `mcp.models.TelemetryAttributeDeclaration`, `mcp.models.PropertyDeclaration`,
   and `mcp.models.CommandDeclaration` each have `implements: list[str] | None
   = None`, populated by `from_domain`.

8. The `tests/integration/schemas/read_blueprint.json` snapshot is regenerated
   and shows `implements` as an optional array-of-strings property on the
   `TelemetryAttributeDeclaration`, `PropertyDeclaration`, and
   `CommandDeclaration` schemas.

9. Unit tests cover:
   - `to_telemetry_attribute_declaration` / `to_property_declaration` /
     `to_command_declaration` map `implements` (present → list of strings;
     absent → `None`).
   - MCP declaration models' `from_domain` propagates `implements`.

10. `make check` passes.
