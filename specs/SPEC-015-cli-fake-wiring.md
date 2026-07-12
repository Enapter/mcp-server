# SPEC-015: CLI fake:// Wiring and filesystem.EnapterAPI Removal

## Context

SPEC-014 introduced `fake.EnapterAPI`, a programmable fake selected by a
`fake://` URL. The CLI currently only constructs `http.EnapterAPI` and
`filesystem.EnapterAPI` (the `filetree://` adapter from SPEC-011/SPEC-012).

`filesystem.EnapterAPI` is used nowhere except tests, cannot express command
behavior, and duplicates `http.EnapterDataMapper` through its pydantic mirror
models. Now that `fake.EnapterAPI` replaces it, the filetree adapter and its
entire model layer are dead code.

This spec wires `fake://` into the CLI and deletes `filesystem.EnapterAPI` and
its models. It supersedes SPEC-011 and SPEC-012.

## Architectural Decisions

### 1. URL-scheme adapter selection

`serve_command._make_enapter_api` selects the adapter by URL scheme:

```python
parsed = urllib.parse.urlparse(url)
if parsed.scheme == "fake":
    return fake.EnapterAPI.from_url(url)
if parsed.scheme in ("http", "https"):
    return http.EnapterAPI(base_url=url)
raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")
```

- `fake://?...` → `fake.EnapterAPI.from_url(url)` (per SPEC-014).
- `http`/`https` → `http.EnapterAPI` (unchanged).
- `filetree` is no longer special-cased; a `filetree://` URL now hits the
  unknown-scheme branch and raises `ValueError`.

No new CLI flags. The existing `--enapter-http-api-url` carries the scheme, as
it did for `filetree://`.

`serve_command.py` adds `fake` to its `from enapter_mcp_server import ...`
line; `filesystem` stays, since `serve_command` still uses
`filesystem.SkillProvider` for skill plugins. The `_make_enapter_api` return
type becomes `http.EnapterAPI | fake.EnapterAPI`.

`tests/unit/cli/test_serve_command.py` is updated: the
`test_filetree_url_creates_filesystem_adapter` test is replaced by one
asserting `fake://?state=<module>` constructs a `fake.EnapterAPI`; the
`http`/`https`, unsupported-scheme, and empty-URL tests remain. The test's
imports drop `filesystem` and add `fake`.

### 2. Delete filesystem.EnapterAPI and its models

Remove:

- `src/enapter_mcp_server/filesystem/enapter_api.py`
- `src/enapter_mcp_server/filesystem/models/` (the entire package — device,
  rule, site, aggregates, and the Literal type aliases)
- `tests/unit/filesystem/test_enapter_api.py`
- `tests/unit/filesystem/models/` (model round-trip tests)

### 3. SkillProvider stays

`filesystem/skill_provider.py` is unrelated production code (reads skill-plugin
files in `serve_command`). It stays. `filesystem/__init__.py` is updated to
export only `SkillProvider`. The `filesystem/` package survives, slimmed.

## Constraints

- No new CLI flags or server config fields.
- `http`/`https` behavior is unchanged.
- `filetree://` raises `ValueError` (no longer a recognized scheme).
- `filesystem.SkillProvider` is untouched.
- `mcp` layer never imports `fake` (existing layering rule).
- Change to adapter selection is limited to `serve_command.py`.

## Acceptance Criteria

1. **fake scheme wired.** `--enapter-http-api-url fake://?state=<module>`
   constructs a `fake.EnapterAPI` via `from_url`.

2. **filetree removed.** `--enapter-http-api-url filetree:///state` raises
   `ValueError`.

3. **HTTP regression.** `https://api.enapter.com` constructs `http.EnapterAPI`
   unchanged.

4. **filesystem.EnapterAPI gone.** `filesystem/enapter_api.py` and
   `filesystem/models/` do not exist. No remaining import references them.

5. **SkillProvider intact.** `filesystem.SkillProvider` is importable and
   unchanged; `filesystem/__init__.py` exports only `SkillProvider`.

6. **CLI unit tests updated.** `tests/unit/cli/test_serve_command.py` asserts
   `fake://?state=<module>` constructs a `fake.EnapterAPI` and that
   `filetree://` raises; the `http`/`https` and unsupported-scheme tests remain.

7. `make check` and `make test` pass (with the filetree tests removed).
