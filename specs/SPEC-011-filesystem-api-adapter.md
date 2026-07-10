# SPEC-011: Filesystem EnapterAPI Adapter

## Context

The MCP server talks to the Enapter Cloud through the `core.EnapterAPI` port,
currently implemented solely by `http.EnapterAPI` (the real REST API client).
For local development, testing, and agent-driven acceptance tests (SPEC-013)
we need a substitute API that agents and developers can read from and write to
without touching production data.

The adapter must be file-backed — when the URL says `filetree://`, data really
lives in files on disk. No in-memory cache, no opaque state: every operation
reads or writes YAML files that a human or agent can inspect directly.

## Architectural Decisions

### 1. filesystem.EnapterAPI — file-backed, no cache

A new driven adapter `filesystem.EnapterAPI` implementing the
`core.EnapterAPI` Protocol. Every operation reads from or writes to YAML files
on disk — no in-memory cache.

Directory layout (one file per aggregate):

```
state/
  sites/
    <site_id>.yaml              → SiteAggregate (site + devices)
  rule_engines/
    <site_id>.yaml              → RuleEngineAggregate (rule engine + rules)
```

Two aggregates with consistency boundaries:

- **Site aggregate** (`SiteAggregate`): site metadata + devices list. Device
  slug uniqueness enforced within the file.
- **Rule engine aggregate** (`RuleEngineAggregate`): rule engine + rules list.
  Rule slug uniqueness enforced within the file.

CRUD maps to single-file read-modify-write operations:

- `list_sites()` → glob `sites/*.yaml`, yield site from each `SiteAggregate`
- `list_devices(site_id)` → read one `SiteAggregate`, yield its devices
- `get_device(device_id)` → scan all `SiteAggregate` files, match by id or slug
- `get_rule_engine(site_id)` → read one `RuleEngineAggregate`
- `list_rules(site_id)` → read one `RuleEngineAggregate`, yield its rules
- `get_rule(site_id, rule_id)` → read one `RuleEngineAggregate`, match by id or slug
- `create_rule(site_id, ...)` → read `RuleEngineAggregate`, enforce slug
  uniqueness, append rule, write back atomically
- `update_rule_script(...)` → read, find rule by id or slug, modify, write back
- `delete_rule(...)` → read, find rule by id or slug, remove, write back

Lives in `src/enapter_mcp_server/filesystem/enapter_api.py`, parallel to
`http.EnapterAPI`. Implements the async context manager protocol for CLI
wiring compatibility (`async with filesystem.EnapterAPI(...) as api:`).

Methods not yet relevant to any scenario return empty results or raise
`NotImplementedError`. Implemented incrementally as scenarios require.

 ### 3. Pydantic models for YAML serialization

`filesystem/models/` contains pydantic models mirroring domain types, with
bidirectional conversion — `from_domain` classmethods (domain → pydantic, like
`mcp/models/`) plus `to_domain` methods (pydantic → domain, for reading YAML
back into domain objects). One class per file.

```
filesystem/
  enapter_api.py                  ← file I/O, uses models for (de)serialization
  models/
    site.py                       ← Site
    site_status.py                ← SiteStatus
    site_aggregate.py             ← SiteAggregate (site + devices)
    device.py                     ← Device
    rule.py                       ← Rule
    rule_script.py                ← RuleScript
    rule_engine.py                ← RuleEngine
    rule_engine_aggregate.py      ← RuleEngineAggregate (rule engine + rules)
    access_role.py                ← Literal type alias
    connectivity_status.py        ← Literal type alias
    device_type.py                ← Literal type alias
    rule_engine_state.py          ← Literal type alias
    rule_runtime_version.py       ← Literal type alias
    rule_state.py                 ← Literal type alias
  skill_provider.py               ← existing
```

Enum fields use `Literal` type aliases — same convention as `mcp/models/`:

```python
class Site(pydantic.BaseModel):
    id: str
    name: str
    timezone: str
    authorized_role: Literal["readonly", "user", "owner", "installer", "vendor", "system"]
    status: SiteStatus | None = None

    @classmethod
    def from_domain(cls, site: domain.Site) -> Self: ...
    def to_domain(self) -> domain.Site: ...
```

Reading YAML: `yaml.safe_load` → `model_validate` → `to_domain()`.
Writing YAML: `from_domain()` → `model_dump(mode="json", exclude_none=True)` → `yaml.dump`.

Pydantic handles validation, enum conversion, and `None` exclusion natively.
No changes to domain types or core.

## Implementation Phases

### Phase 1: Adapter + models

- Pydantic models in `filesystem/models/` (one class per file) for Site,
  SiteStatus, SiteAggregate, Device, Rule, RuleScript, RuleEngine,
  RuleEngineAggregate — each entity model with `from_domain` + `to_domain`
- `filesystem.EnapterAPI` with read/write methods using aggregate models for
  YAML serialization
- ID validation (`^[a-z0-9]([a-z0-9]-?)*[a-z0-9]$`) on all ID parameters
- Slug-based lookups (match by id or slug) for rules and devices
- Async context manager
- Unit tests: round-trip (domain → YAML → domain), CRUD against a temp
  directory, slug lookups, slug uniqueness enforcement

## Constraints

- No new MCP tools
- No new server config flags or modes
- No in-memory caching — every operation hits disk
- `mcp` layer never imports `filesystem` (existing layering rule)
- All entity IDs (`site_id`, `device_id`, `rule_id`) validated against
  `^[a-z0-9]([a-z0-9]-?)*[a-z0-9]$` — covers both UUIDs and slugs, prevents
  path traversal (no `/`, `..`, or special characters).
- `rule_id` and `device_id` parameters accept either UUID or slug; lookups
  match by `id == value or slug == value`.
- `create_rule` enforces slug uniqueness per rule engine (matching cloud
  semantics). Device slug uniqueness enforced within site aggregate.
- `create_rule` sets state to `STARTED` when `disabled=False`, `STOPPED` when
  `disabled=True` (matching cloud semantics)
- Device manifest is not persisted — `from_domain` drops it, `to_domain`
  returns `None`. Manifest-dependent features (blueprint reads, command
  resolution) are not supported through this adapter.
- Writes are atomic (temp file + `os.replace`) to prevent corruption on crash
- Missing entities raise domain errors (`core.RuleNotFound`,
  `core.DeviceNotFound`, etc.), not raw `FileNotFoundError`
