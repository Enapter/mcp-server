# SPEC-010: Serve Skills as a Tool, Not Resources

## Context

SPEC-009 served the `rule-creator` skill to MCP clients as **resources** via
FastMCP's `SkillProvider` (`supporting_files="resources"`). The mechanism is
correct on paper but fails in practice for a class of clients: some MCP clients
(including several popular agents) only load a resource into the model's context
when a human manually selects it. The `rule-creator` knowledge therefore never
reaches the model unless a user intervenes, which defeats the point of exposing
it. Tools, by contrast, are invoked by the model autonomously.

Separately, the community convention for skills (the [Agent
Skills](https://agentskills.io) standard, implemented by Claude Code and
OpenCode) treats a skill's supporting files as regular filesystem paths that the
host agent reads with its native file-read tool. That model assumes the agent
has filesystem access to the skill directory. An MCP server breaks that
assumption: the skill content lives on the *server's* filesystem and the client
has no tool to read arbitrary files there. Serving skills over MCP therefore
requires exposing the file-read through our own tool surface.

Two prerequisites make the new design possible:

- The `rule-creator` skill's `SKILL.md` citations are files-only upstream
  (every load target is a specific file path like `references/v3/README.md` or
  `references/v3/api.md`; no directory citations). `pathlib.PurePosixPath`
  handles the one remaining markdown-syntax artifact — the leading `./` on
  relative-link hrefs — at construction time (decision 3).
- The `--skill-plugins` flag and `ENAPTER_SKILL_PLUGINS` env var point at the
  skill plugins directory. The Dockerfile `COPY`s selected skills into the
  expected structure and `make serve` runs via Docker.

This spec supersedes the resources-based design in SPEC-009 decisions 1, 2, 4,
and 8 (decision 2 / AC 2 included because this spec removes
`ServerConfig.rule_creator_skill_path`), and the SPEC-009 constraints /
acceptance criteria that mandate resources or `SkillProvider`.

## Architectural Decisions

### 1. Serve skills through a single `read_skill` tool

Replace the `SkillProvider` resources surface with one MCP tool on the driving
adapter:

```python
async def read_skill(
    self,
    name: Literal["enapter:rule-creator"],
    file: str = "SKILL.md",
) -> str
```

- `file` defaults to `"SKILL.md"`, so `read_skill("enapter:rule-creator")`
  returns the skill's entry index (its `SKILL.md`, with the decision tree). This
  is the load/invoke step.
- `file="references/v3/api.md"` returns that file's content. This is the
  supporting-file read that the community model does via the host agent's
  native file-read tool; we expose it explicitly because the MCP client has no
  other filesystem access to the server.

The tool is read-only (`readOnlyHint=True`, `destructiveHint=False`), registered
with title `"Read Skill"`. **The `str`-to-`PurePosixPath` conversion happens
only at this layer** — every layer below receives a `pathlib.PurePosixPath`.

Rationale: tools are model-invoked and auto-called; resources are client-gated
behind manual user selection in several clients. Skills exist to drive the
model's behavior on rule-editing tasks, so they must reach the model without a
human in the loop.

### 2. Three-tier flow following the existing layering

`read_skill` follows the exact same flow as every other tool
(`search_rules`, `create_rule`, …): the MCP adapter calls only the application
server; the application server orchestrates a port; a driven adapter implements
the port. The MCP adapter never touches a driven adapter or the filesystem.

```
mcp.Server.read_skill(name, file="SKILL.md")               # driving adapter (str → PurePosixPath conversion here)
  └─► core.ApplicationServer.read_skill(name, file)         # application: orchestrates (async)
        ├─► core.SkillProvider.load_skill(name)              # port
        │     ▲ implemented by filesystem.SkillProvider (driven adapter)
        └─► domain.Skill.read(file) -> str                  # domain: exact-match against PurePosixPath keys
```

Dependency arrows (unchanged project rules):

```
domain  ◄── core ◄──┬── mcp        (mcp depends ONLY on core + domain)
                    └── filesystem (filesystem depends on core + domain, like http does)
                          ▲
                          └── cli   (composition root binds the adapter)
```

`mcp` never imports `filesystem`. `core.ApplicationServer` owns no MCP concerns; it
calls the `core.SkillProvider` port and the `domain.Skill` method. The
`filesystem.SkillProvider` adapter owns all filesystem logic and depends
on `core` (the port) + `domain` (the data). This mirrors `core.EnapterAPI` end
to end: port in `core`, driven adapter in a peer package, application server as
the orchestrator, MCP adapter as the driving caller.

### 3. Domain: `Skill` owns exact-match selection via `PurePosixPath`

`domain.Skill` is a domain concept in this product (the server serves skills to
agents), so it lives in `domain/`. It is **not** anemic — it owns the "the
requested file must be one of this skill's files" invariant:

```python
@dataclass(frozen=True)
class Skill:
    name: str
    files: dict[pathlib.PurePosixPath, str]

    def read(self, path: pathlib.PurePosixPath) -> str:
        if path not in self.files:
            raise SkillFileNotFound(path, valid=sorted(self.files))
        return self.files[path]
```

- **Path types, not strings.** `PurePosixPath` handles `./` normalization
  automatically at construction (`PurePosixPath("./refs/api.md")` equals
  `PurePosixPath("refs/api.md")`), eliminating the need for a custom
  `normalize_skill_path` function. Keys and lookups are `PurePosixPath`; no
  manual string transforms.
- **Both new errors live in `domain/errors.py`**: `SkillFileNotFound` (raised by
  `Skill.read` on a miss; takes `path: PurePosixPath` and
  `valid: list[PurePosixPath]`) and `SkillNotFound` (raised by the provider on
  unknown skill name; takes `name: str`). `domain` imports `pathlib` for
  `PurePosixPath` (pure path computation, no filesystem access).

Putting selection on `Skill` means the invariant travels with the data; the
application server is pure orchestration.

### 4. Core: `SkillProvider` port + `ApplicationServer.read_skill` (async)

- **Port** — `core.SkillProvider(Protocol)` with a single method
  `load_skill(name: str) -> domain.Skill`. Unknown `name` raises
  `domain.SkillNotFound`. The port is synchronous:
  skill loading is a fast local-disk read, performed eagerly at startup
  (decision 9).
- **Application server** — `core.ApplicationServer.__init__` takes
  `skill_provider: SkillProvider | None = None` (default `None` preserves
  existing call sites and the read-only deployment). It gains:

  ```python
  async def read_skill(self, name: str, file: pathlib.PurePosixPath) -> str:
      if self._skill_provider is None:
          raise RuntimeError("Skill provider is not configured")
      skill = self._skill_provider.load_skill(name)
      return skill.read(file)
  ```

  `async def`, matching every other `ApplicationServer` method. **No default on
  `file`** — defaults are a presentation concern and live only on the MCP tool
  (decision 1). The method takes required `(name, file)`. No `auth` parameter:
  skills are server-side documentation, not user-scoped data. The `None` guard
  is a defensive runtime check; in practice the MCP layer never registers the
  tool when skills are disabled (decision 7), so this branch is unreachable.

- **No `skills_enabled` property.** The MCP layer does not query the app for
  capability. Tool registration is gated by `ServerConfig.skills_enabled`
  (decision 7), set by the CLI based on whether the `--skill-plugins` path was
  provided.

### 5. `filesystem.SkillProvider` driven adapter

New infrastructure package `filesystem/` (peer of `http/`), containing driven
adapters that read from disk. For skills it houses:

- `filesystem/skill_provider.py` — `SkillProvider` with a `from_directory`
  classmethod that scans a **skill plugins directory** and dynamically discovers
  all skills. The expected structure is:

  ```
  <path>/
    <namespace>/          # e.g. "enapter"
      skills/
        <skill-name>/     # e.g. "rule-creator"
          SKILL.md
          references/...
  ```

  Each namespace directory is treated as a **skill plugin**. The provider walks
  each plugin's `skills/` subdirectory, loads every directory containing a
  `SKILL.md` as a `domain.Skill`, and assigns it the namespaced name
  `<namespace>:<skill-name>` (e.g. `enapter:rule-creator`). No skill names are
  hard-coded — what's in the directory is what gets served. Which skills exist
  in the Docker image is controlled at build time by selective `COPY`
  instructions.

  Internally, three methods each handle one level of the tree:
  `from_directory` validates the path and iterates plugin directories;
  `_load_plugin` walks a plugin's `skills/` tree; `_load_files` reads all files
  from a single skill directory into a `dict[PurePosixPath, str]`.

- `filesystem/__init__.py` exports the adapter.

This is the single place that imports `pathlib.Path` and reads disk for skills.
Neither `core`, `domain`, nor `mcp` imports this package; only `cli` does, to
construct it. Symlink hardening is intentionally **not** added: skill content is
vendored from a controlled upstream (`Enapter/skills`), not user-supplied.

### 6. Exact-match against pre-read `PurePosixPath` keys; no FS resolution at serve

The security boundary is `domain.Skill.files`, built once at load time. At serve
time, `file` is a `PurePosixPath` (constructed from the MCP tool's string param)
and exact-matched against the pre-read `PurePosixPath` keys. There is no
`Path.resolve()` / `is_relative_to()` on the serve path, and the filesystem is
never re-read based on a caller-supplied value. A traversal attempt like
`../../etc/passwd` or `references/../SKILL.md` is not a stored key and is
rejected; there is no resolution logic to subvert. This keeps serve-time work
to a `PurePosixPath` construction + dict lookup with no disk I/O.

### 7. MCP: `read_skill` is a plain tool; registration gated by config

The MCP `Server` no longer has a `_register_skills` method, no
`skill_provider` constructor argument, and no `pathlib` / `filesystem` / FastMCP
`SkillProvider` references. `read_skill` is just another method on `Server`,
registered through `_register_tools` like every other tool:

- `Server.read_skill(name, file="SKILL.md")` converts `file` to a
  `PurePosixPath` and delegates: `return await self._app.read_skill(name,
  pathlib.PurePosixPath(file))`.
- **Registration gate is `ServerConfig.skills_enabled`, not an app property.**
  `_read_only_tools` includes `(self.read_skill, "Read Skill")` iff
  `self._config.skills_enabled`. This follows the same pattern as
  `command_execution_enabled` and `rule_editing_enabled` — all tool-registration
  gates are config flags, not runtime capability queries.

The tool's `description` is a static string explaining how to use `read_skill`
(load `SKILL.md` first, then pass a cited reference path). It does **not**
embed the skill's frontmatter description — the agent is directed to
`read_skill` by the `create_rule` / `edit_rule` docstrings (decision 12), so
description-first discovery is unnecessary. The `Literal["enapter:rule-creator"]`
on `name` advertises the served skill names as a JSON schema enum.

There is deliberately **no `list_skills` tool and no manifest/file-tree
payload**. `SKILL.md` alone is the discovery surface for supporting files,
mirroring the community model.

### 8. No pagination

Skill files are bounded by authoring (largest is ~111 lines / 5.4 KB;
`SKILL.md` is 63 lines; the whole skill is ~676 lines / ~33 KB). No single file
threatens a context window. `read_rule` paginates because user-written Lua is
unbounded; authored skill docs are bounded by design, and the skill's own
structure (thin `SKILL.md` index → focused ≤111-line reference files) *is* the
pagination. If a file ever outgrows context, the fix is to split it in
`Enapter/skills`, not to add `offset`/`limit` here. `read_skill` returns the
whole file. Matches the community model (skill files are read whole) and keeps
the tool a pure lookup.

### 9. Composition root: build the adapter before the `TaskGroup`, then inject

`cli/serve_command.py` (the composition root) is the only place that knows about
both `filesystem.SkillProvider` and `mcp.Server`. To preserve SPEC-009's
clean-startup-failure property, the adapter must eager-load **before** the async
`TaskGroup` is entered, so a missing directory, unreadable file, or malformed
`SKILL.md` surfaces as a normal exception rather than one wrapped by the async
runtime's `ExceptionGroup` + `CancelledError`. Concretely:

```python
# pre-TaskGroup (synchronous, eager):
skill_plugins_path = (
    pathlib.Path(args.skill_plugins) if args.skill_plugins else None
)
skill_provider = (
    filesystem.SkillProvider.from_directory(skill_plugins_path)
    if skill_plugins_path is not None
    else None
)

config = mcp.ServerConfig(
    ...,
    skills_enabled=skill_provider is not None,
)

async with asyncio.TaskGroup() as task_group:
    async with http.EnapterAPI(...) as enapter_api:
        app = core.ApplicationServer(
            enapter_api=enapter_api, skill_provider=skill_provider
        )
        async with mcp.Server(app=app, config=config, task_group=task_group):
            await asyncio.Event().wait()
```

Skills are independent of rule editing — a user may have the skill knowledge
without needing the server to serve it. If `--skill-plugins` is not provided,
the provider is `None`, `skills_enabled` is `False`, and the `read_skill` tool
is not registered. No error is raised. If the path is provided but the directory
is missing or malformed, the adapter's `from_directory` raises a clean
exception before the `TaskGroup`.

The `--skill-plugins` flag and `ENAPTER_SKILL_PLUGINS` env var replace the old
`--rule-creator-skill-path` / `ENAPTER_RULE_CREATOR_SKILL_PATH`. They point at
the skill plugins root directory, not a single skill directory.

### 10. `ServerConfig` gains `skills_enabled`

`ServerConfig` gains `skills_enabled: bool = False`. This is a presentation-layer
flag: the CLI sets it based on whether a skill provider was constructed. The MCP
layer reads it to decide tool registration (decision 7). It is **not** a
capability query on the app — the app always accepts an optional
`SkillProvider | None` and guards at runtime (decision 4).

`ServerConfig.rule_creator_skill_path` (from SPEC-009) is removed. A filesystem
path is infrastructure wiring, not server configuration; it lives only in the
CLI flag/env and is consumed there to build the adapter. (Supersedes SPEC-009
decision 2 / AC 2.)

### 11. Resources surface

With `SkillProvider` gone, the server no longer serves any MCP resources.
`Client.list_resources()` in `mcp/client.py` and the `list_resources` CLI
command are general MCP protocol tools (they accept `--address` and can query
any server) and are unchanged.

### 12. Point agents at the tool in rule-editing docstrings

Replace the "List MCP resources to find it" line in the `create_rule` and
`edit_rule` docstrings with an instruction to call `read_skill` first, e.g.:

> This server exposes the `rule-creator` skill via the `read_skill` tool. Call
> `read_skill("enapter:rule-creator")` to load it before touching any rule code.

This is the nudge that makes agents actually walk the disclosure ladder
(load `SKILL.md` → follow its decision tree → read the cited reference file).

### 13. Docker: build-time skill selection, Docker-based local dev

The Dockerfile `COPY`s selected skills into the expected plugins structure:

```dockerfile
ENV ENAPTER_SKILL_PLUGINS=/app/skill-plugins
COPY vendor/enapter-skills/plugins/enapter/skills/rule-creator ./skill-plugins/enapter/skills/rule-creator
```

Which skills are in the image is a build-time decision controlled by `COPY`
instructions. `make serve` builds the image (cached layers, fast) and runs it
via Docker, eliminating the need for symlinks or Makefile env exports. Tests
run via pipenv and point at the vendor submodule directly.

## Constraints

- Serve skills through the `read_skill` tool only. No MCP resources served by
  this server, no resource templates, no FastMCP `SkillProvider`, no
  manifest/file-tree payload, no `list_skills` tool, no pagination
  (`offset`/`limit`). (`Client.list_resources` and the `list_resources` CLI
  command are general protocol tools and remain.)
- Layering: `mcp` depends only on `core` + `domain`. `mcp` must not import
  `filesystem`. `filesystem` depends on `core` + `domain`. Only `cli` binds the
  adapter.
- The `str`-to-`PurePosixPath` conversion happens only at the MCP tool layer;
  the application server, port, and domain all use `pathlib.PurePosixPath`.
- Path handling: the caller-supplied `file` string is converted to a
  `PurePosixPath` at the MCP layer, then exact-matched against pre-read
  `PurePosixPath` keys. Never resolve, normalize via the filesystem, or re-read
  disk based on a caller-supplied value at serve time.
- All new errors live in `domain/errors.py` (both `SkillFileNotFound` and
  `SkillNotFound`); migrating the existing `core/errors.py` errors to `domain/`
  is out of scope for this spec.
- `read_skill` is registered iff `ServerConfig.skills_enabled` is `True`. The CLI
  sets this flag based on whether a skill provider was constructed. Skills are
  independent of rule editing — they can be enabled without rule editing and
  vice versa.
- The adapter must eager-load before the `TaskGroup` is entered, so load/parse
  failures surface as clean startup errors.
- The skill plugins directory structure (`<namespace>/skills/<skill>/`) is
  dynamic discovery — no hard-coded skill names. Which skills exist in a given
  deployment is controlled by what files are present (Docker `COPY` at build
  time, submodule content in tests).
- Do not change the `rule-creator` skill content from this repo; it is owned by
  `Enapter/skills` and consumed read-only via the submodule.

## Acceptance Criteria

1. `domain.Skill` exists with `name`, `files: dict[pathlib.PurePosixPath, str]`,
   and a `read(path: pathlib.PurePosixPath) -> str` method. The method
   exact-matches `path` against `self.files`. On miss it raises
   `domain.SkillFileNotFound` (taking `PurePosixPath` args) with
   `sorted(self.files)` in the message. `SkillFileNotFound` and `SkillNotFound`
   live in `domain/errors.py`. No custom `normalize_skill_path` function exists.

2. `core.SkillProvider` is a `Protocol` with `load_skill(name: str) ->
   domain.Skill`, defined alongside the existing core ports; unknown `name`
   raises `domain.SkillNotFound`. `ApplicationServer.__init__` accepts
   `skill_provider: SkillProvider | None = None`. No `skills_enabled` property
   on `ApplicationServer`.

3. `async def ApplicationServer.read_skill(name: str, file:
   pathlib.PurePosixPath) -> str` exists, takes **required** `name` and `file`
   (no default), and guards on `self._skill_provider is None`. It has no `auth`
   parameter and no filesystem imports.

4. `filesystem.SkillProvider` implements `core.SkillProvider`.
   `from_directory(path)` scans `<namespace>/skills/<skill>/` dynamically,
   loads every directory containing a `SKILL.md`, and assigns namespaced names
   (`<namespace>:<skill-name>`). No hard-coded skill names. Internally uses
   `_load_plugin` and `_load_files`. No frontmatter is parsed. It is the only
   component that imports `pathlib.Path` or reads disk for skills. No component
   in `core/`, `domain/`, or `mcp/` imports `filesystem`.

5. `mcp.Server` has no `_register_skills` method, no `skill_provider`
   constructor argument, and no reference to FastMCP `SkillProvider` or the
   `filesystem` package. `read_skill(name: Literal["enapter:rule-creator"],
   file: str = "SKILL.md") -> str` is `async def`, is registered as a read-only
   tool with title `"Read Skill"` only when `self._config.skills_enabled` is
   true, and its body converts `file` to `pathlib.PurePosixPath(file)` and
   delegates to `await self._app.read_skill(name, ...)`. The tool `description`
   is a static string (no frontmatter embedding).

6. `read_skill("enapter:rule-creator")` returns the content of `SKILL.md` (the
   default for `file`). `read_skill("enapter:rule-creator", "references/v3/api.md")`
   returns that file's content. `read_skill("enapter:rule-creator",
   "./references/v3/api.md")` also resolves (`PurePosixPath` strips `./`).
   Any `file` value that is not a stored key — including directory forms like
   `references/v3/` and traversal attempts like `../SKILL.md` or
   `references/../SKILL.md` — raises `domain.SkillFileNotFound` listing the
   valid keys. No caller-supplied path is ever resolved via the filesystem.

7. `cli/serve_command.py` provides `--skill-plugins` / `ENAPTER_SKILL_PLUGINS`,
   constructs `filesystem.SkillProvider.from_directory(path)` **before** entering
   the `async with TaskGroup()` when the path is provided, passes it (or `None`)
   into `ApplicationServer(..., skill_provider=...)` inside the `TaskGroup`, and
   sets `skills_enabled=skill_provider is not None` in `ServerConfig`. No
   error is raised when the path is not provided. `ServerConfig` has no
   `pathlib` reference and no `rule_creator_skill_path`.

8. The `create_rule` and `edit_rule` docstrings no longer mention MCP resources
   or `list_resources`; they instruct the agent to call
   `read_skill("enapter:rule-creator")` first.

9. `Client.list_resources()` in `mcp/client.py` and the `list_resources` CLI
   command (`cli/list_resources_command.py` + its `cli/app.py` wiring) are
   unchanged — they are general MCP protocol tools.

10. The full tool-count matrix holds: default config → 7; command execution
    only → 8; rule editing + skills (no command execution) → 11; command
    execution + rule editing + skills → 12. The integration tests assert the
    matrix.

11. The `create_rule` and `edit_rule` schema snapshots
    (`tests/integration/schemas/{create_rule,edit_rule}.json`) are regenerated
    to reflect the updated docstrings, and a `read_skill.json` snapshot is
    added asserting the `Literal` enum on `name` (`enapter:rule-creator`), the
    `file` param defaulting to `"SKILL.md"`, and the read-only annotations.

12. `mcp` unit tests for `read_skill` inject a fake `core.SkillProvider`
    (and/or construct `domain.Skill` directly); they do not touch disk.
    `filesystem.SkillProvider` has its own tests against tmp directories
    asserting namespaced discovery, multiple plugins, and file loading.
    `domain.Skill.read` has unit tests covering `PurePosixPath` normalization
    and the miss-error.

13. A Docker image built with `make docker-image` starts, exposes the
    `read_skill` tool when `ENAPTER_SKILL_PLUGINS` is set, and an MCP
    `tools/list` against it includes `read_skill`. `make serve` builds the image
    and runs the server via Docker.

14. `make check` passes.
