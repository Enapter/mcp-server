# SPEC-012: CLI Wiring for filesystem.EnapterAPI

## Context

SPEC-011 introduced `filesystem.EnapterAPI`, a file-backed adapter implementing
the `core.EnapterAPI` Protocol. Currently the CLI only constructs
`http.EnapterAPI`. We need a way to select the filesystem adapter from the CLI
without adding new flags or modes.

## Architectural Decisions

### 1. URL-scheme adapter selection

The existing `--enapter-http-api-url` flag (default
`https://api.enapter.com`) determines the adapter based on URL scheme:

- `filetree:///path/to/state` → `filesystem.EnapterAPI(state_dir=path)`
- `https://...` → `http.EnapterAPI(base_url=url)` (existing behavior)

A branch in `serve_command.py` parses the scheme and constructs the
appropriate adapter. The rest of the server is unaware.

### 2. URL parsing with stdlib

Use `urllib.parse.urlparse` to detect the scheme and extract the path. No
string prefix hacks.

```python
parsed = urllib.parse.urlparse(url)
if parsed.scheme == "filetree":
    if parsed.netloc:
        raise ValueError(...)
    if not parsed.path or not parsed.path.startswith("/"):
        raise ValueError(...)
    return filesystem.EnapterAPI(state_dir=pathlib.Path(parsed.path))
if parsed.scheme in ("http", "https"):
    return http.EnapterAPI(base_url=url)
raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")
```

`filetree://` URLs must have an absolute path and no host component.
Unknown schemes are rejected.

## Constraints

- No new CLI flags
- No new server config fields
- `mcp` layer never imports `filesystem` (existing layering rule)
- Change limited to `serve_command.py`

## Acceptance Criteria

- `filetree:///tmp/state` → constructs `filesystem.EnapterAPI(state_dir=Path("/tmp/state"))`
- `https://api.enapter.com` → constructs `http.EnapterAPI(base_url=...)` (regression)
- Both adapters used identically via `async with` — no changes to the server
  startup path beyond adapter construction
- `filetree://` without absolute path raises `ValueError`
- `filetree://localhost/state` (with host) raises `ValueError`
- Unknown schemes (e.g. `ftp://`) raise `ValueError`
- Return type is a union of concrete adapter classes (the `core.EnapterAPI`
  Protocol does not include `__aenter__`/`__aexit__`)
