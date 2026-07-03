# SPEC-009: Serve and Bundle Enapter Skills

## Context

The rule-editing tools (`create_rule`, `edit_rule`, `delete_rule`) require the
assistant to understand the Enapter Rule Engine: the v1/v3 Lua APIs, scheduling
patterns, device interaction, and known pitfalls. That knowledge lives in the
`rule-creator` skill maintained in the
[`Enapter/skills`](https://github.com/Enapter/skills) repository, alongside
other Enapter skills (e.g. `blueprint-creator`). Nothing in the server currently
delivers any of this knowledge to the assistant.

This spec does two things:

- **Serve** selected skills to MCP clients as MCP resources, so an assistant can
  load the knowledge on demand without the skill being installed client-side.
- **Bundle** the served skill content into the Docker image (the canonical
  distribution artifact), so a deployed server can actually serve it.

Only `rule-creator` is exposed for now. Each exposed skill is configured
individually, so adding a skill later (including a non-Enapter one from a
different source) is independent of the others.

## Architectural Decisions

### 1. Serve skills as MCP resources via `SkillProvider`

Register one FastMCP `SkillProvider` per served skill (in a new
`Server._register_skills`). Each provider exposes that skill's `SKILL.md` and
reference files as individual MCP resources. The assistant follows the skill's
decision tree and pulls only the references it needs, keeping token usage
efficient.

Use `supporting_files="resources"`, not resource templates — resource templates
are poorly supported by MCP clients. Eager resource discovery has been verified
to work with OpenCode and Codex; other listed clients (e.g. Claude Desktop)
should be checked separately.

### 2. Configure each skill individually; only `rule-creator` for now

Each skill the server can serve is its own config knob: a `ServerConfig` field,
a CLI flag, and an env var holding the filesystem path to that skill's
directory (the one containing `SKILL.md`). There is no collection-root knob and
no central allowlist. A skill is served iff its path is configured and resolves
on disk (see decision 4).

For now the only such knob is `rule_creator_skill_path`. The server intentionally
does not auto-discover skills from a directory: which skills are served is a
deliberate code-level decision (adding a field + flag + registration call), so
skills present in the submodule but not wired up (e.g. `blueprint-creator`, which
has no corresponding tools on this server) cannot leak to clients.

The resource surface should stay coherent with the tool surface, the same
intent behind the tool kill switches. `rule-creator` maps to the rule-editing
tools; `blueprint-creator` (authoring/publishing blueprints) has no such pair
today and is therefore not served.

Serving `rule-creator` is gated behind `rule_editing_enabled`, since it supports
rule editing. This coupling should be revisited if a skill unrelated to rule
editing is added.

### 3. Vendor `Enapter/skills` as a git submodule

Add `https://github.com/Enapter/skills.git` as a submodule at
`vendor/enapter-skills`, pinned to a specific commit. HTTPS is used (not SSH)
so CI and clean clones can fetch it without key material.

Rationale: the skills repo is the source of truth and must not be copied into
this repo by hand (no manual sync). A submodule pins an exact version to a
server release for reproducibility while keeping the content read-only and
externally maintained.

### 4. Make each skill path configurable

Each served skill has a `ServerConfig.<skill>_skill_path: pathlib.Path` field,
sourced from `ENAPTER_<SKILL>_SKILL_PATH` / `--<skill>-skill-path`, mirroring
the existing config pattern in `cli/serve_command.py`. Paths point directly at
the skill directory, so no assumption about a surrounding collection layout is
baked in.

For `rule-creator`:

- Field: `rule_creator_skill_path`
- Flag: `--rule-creator-skill-path`
- Env: `ENAPTER_RULE_CREATOR_SKILL_PATH`
- Default (CWD-relative): `vendor/enapter-skills/plugins/enapter/skills/rule-creator`

The default resolves correctly in both runtime contexts:

- **Docker**: `WORKDIR /app`, and the Dockerfile copies the subtree to
  `/app/vendor/enapter-skills/plugins/enapter/skills/rule-creator`.
- **Local dev**: launched from the repo root after `git submodule update --init`.

The override exists for developers who want to point at a live sibling checkout
or a skill from another source.

### 5. Fail fast when a configured skill is missing

For each skill the server is configured to serve, `_register_skills` resolves
the path and raises if that directory does not exist, refusing to start.

Rationale: a configured-but-missing skill is a configuration error (forgot
`git submodule update --init`, wrong path), and the tool docstrings promise the
resource to agents. Silently dropping it would break that promise and yield
rules written without the Rule Engine knowledge the skill provides. Surfacing
the error at startup forces the operator to fix it immediately.

This check applies only when a skill is actually configured to be served.
`rule-creator` is served only when `rule_editing_enabled` is on, so a
read-only deployment (rule editing off) boots fine without the submodule.

### 6. Ship each served skill's subtree in Docker

The Dockerfile copies each served skill's subtree (not the entire submodule) to
the same CWD-relative path the skill's default config points at. This keeps the
image lean and mirrors the per-skill independence: enabling a new skill later
means adding its own `COPY` line alongside its config knob. For now:

```dockerfile
COPY vendor/enapter-skills/plugins/enapter/skills/rule-creator \
     ./vendor/enapter-skills/plugins/enapter/skills/rule-creator
```

### 7. Ensure submodule content is present before building

Docker does not initialize submodules; the files must exist in the build
context first. Two consumers build the image and must initialize submodules
beforehand:

- **`Makefile` `docker-image`** runs `git submodule update --init --recursive`
  before `docker build`.
- **CI** (`.github/workflows/ci.yml`) sets `submodules: true` on every
  `actions/checkout` step that feeds a Docker build (the `run_checks`,
  `push_to_docker_hub`, and `push_to_enapter_docker_hub` jobs). `actions/checkout`
  is bumped to `v4` (v2 is deprecated and emits warnings).

### 8. Point agents at the resource in tool docstrings

The `create_rule` and `edit_rule` docstrings tell the assistant the
`rule-creator` skill is exposed as an MCP resource "in case you don't have it
installed" and to list MCP resources to find it. That phrasing conveys the
fallback intent (an agent that already has the skill installed need not reload
it).

## Constraints

- Deliver skills as MCP resources, not resource templates. Use
  `supporting_files="resources"`.
- Do not auto-discover skills from a directory; each served skill is wired up
  explicitly via its own config knob.
- Do not publish skill content to PyPI; the server is distributed only as the
  Docker image and the hosted service. The submodule lives in the repo tree, not
  in the installed package.
- Do not vendor skill content by copying it into the source tree; the skills
  repo remains the single source of truth.
- Do not change which tools `rule_editing_enabled` gates.
- When a skill is configured to be served (e.g. `rule-creator` with rule
  editing enabled), the server MUST fail to start if its path is missing.

## Acceptance Criteria

1. `Enapter/skills` is added as a git submodule at `vendor/enapter-skills`,
   pinned to a specific commit, fetchable over HTTPS. `.gitmodules` is committed.

2. `ServerConfig` has a `rule_creator_skill_path: pathlib.Path` field defaulting
   to `pathlib.Path("vendor/enapter-skills/plugins/enapter/skills/rule-creator")`.

3. `cli/serve_command.py` exposes `--rule-creator-skill-path` with `argparse`
   `ArgumentDefaultsHelpFormatter`-visible default sourced from
   `ENAPTER_RULE_CREATOR_SKILL_PATH`, and passes it into `ServerConfig`.

4. `mcp.Server._register_skills`, gated behind `rule_editing_enabled`, resolves
   `rule_creator_skill_path` and registers a `SkillProvider` with
   `supporting_files="resources"`; if the directory does not exist, it raises so
   the server does not start. No directory auto-discovery.

5. The `create_rule` and `edit_rule` docstrings state that the server exposes
   the `rule-creator` skill as an MCP resource "in case you don't have it
   installed" and that the assistant should list MCP resources to find it.

6. The `Dockerfile` copies the `rule-creator` subtree to its CWD-relative
   default path.

7. The `Makefile` `docker-image` target initializes submodules before building.

8. `.github/workflows/ci.yml` initializes submodules for every checkout that
   feeds a Docker build.

9. A Docker image built with `make docker-image` starts, and an MCP
   `resources/list` against it (with rule editing enabled) returns the
   `rule-creator` skill resources and no others.

10. `make check` passes.
