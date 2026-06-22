# SPEC-004: Blueprint ID on Devices

## Context

Multiple devices of the same model and vendor share an underlying blueprint, and
therefore have identical manifests. An agent reading blueprints to learn device
interfaces issues redundant `read_blueprint` calls for same-blueprint devices,
wasting network round-trips and context.

The SDK exposes a stable `blueprint_id` on every device — the platform does not
allow creating a device without specifying a blueprint. Exposing this field on
the MCP `Device` model lets the agent dedupe: same `blueprint_id` ⇒ identical
manifest ⇒ read once, reuse for every matching device.

`device.type` (LUA, VIRTUAL_UCM, GATEWAY, ...) is the transport category, not a
blueprint identifier. `blueprint_id` is a separate field that fills a gap the
existing model has no equivalent for.

## Architectural Decisions

1. **Add `blueprint_id: str` to `domain.Device` (required).** All devices have
   a blueprint. Sourced directly from the SDK's `Device.blueprint_id`.

2. **Flow the field end-to-end** through `core.DeviceDTO` and
   `mcp.models.Device` so the value propagates from SDK → DTO → domain → MCP
   response without loss.

3. **Dedup is agent-side, guided by the `search_devices` docstring.** Paginating
   a site in BASIC view is cheap; the agent sees `blueprint_id` on every device
   and can identify which devices share a blueprint. The `search_devices`
   docstring guides the agent: devices sharing the same `blueprint_id` have
   identical manifests, so `read_blueprint` need only be called once per unique
   `blueprint_id`. `read_blueprint`'s parameter list is unchanged.

## Constraints

- Do not change `read_blueprint`'s parameter list or behavior.
- Do not add a `blueprint_id` filter to `search_devices` or
  `DeviceSearchQuery`.
- Do not change `device.type` semantics or values.
- Do not add profile-related fields or concepts (separate specs).

## Acceptance Criteria

1. `domain.Device` has `blueprint_id: str` (required, not optional).

2. `core.DeviceDTO` has `blueprint_id: str` (required).

3. `mcp.models.Device` exposes `blueprint_id: str` (required), populated by
   `from_domain`.

4. `EnapterDataMapper.to_device_dto` maps `blueprint_id` from the SDK `Device`
   object's `blueprint_id`.

5. The `search_devices` tool docstring includes guidance that devices sharing
   the same `blueprint_id` have identical manifests, and that `read_blueprint`
   need only be called once per unique `blueprint_id`.

6. The `tests/integration/schemas/search_devices.json` snapshot is regenerated
   and shows `blueprint_id` as a required string field on the Device item
   schema.

7. Unit tests cover:
   - `to_device_dto` maps `blueprint_id` from the SDK object.
   - `mcp.models.Device.from_domain` propagates `blueprint_id`.

8. `make check` passes.
