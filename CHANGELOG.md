## [0.10.0] - 2026-03-24

### 🚀 Features

- *(mcp)* Add mandatory title annotations for tool registrations
- *(docker)* Set 'serve' as default CMD to simplify container usage
- Add configurable CORS support for MCP server
- [**breaking**] Remove latest_telemetry from get_device_details

### 📚 Documentation

- *(readme)* Update guide for connecting AI applications and self-hosting
- *(license)* Add Apache 2.0 license and badge
- Add contributing guide and link it from README
- Add direct email contact for user support

### ⚙️ Miscellaneous Tasks

- Add glama.json manifest
- *(release)* Bump version to 0.10.0

### ◀️ Revert

- Chore: add glama.json manifest
## [0.9.1] - 2026-03-20

### ⚙️ Miscellaneous Tasks

- *(docker)* Ensure reproducible image builds
- *(release)* Bump version to 0.9.1
## [0.9.0] - 2026-03-20

### 🚀 Features

- *(domain)* Introduce SiteSpecification and DeviceSpecification for searches

### 🚜 Refactor

- Implement layered architecture to decouple core logic from MCP
- Isolate domain models from Enapter API contract using DTOs
- Rename 'Context' to 'Details' for domain models and MCP tools
- *(domain)* Move search matching logic into Specifications
- Decorate async generators with enapter.async_.generator

### 🎨 Styling

- Run black and isort to fix formatting issues

### 🧪 Testing

- *(domain)* Add unit tests for search specifications

### ⚙️ Miscellaneous Tasks

- *(.gitignore)* Drop `mcp_client_config.json`
- *(setup)* Upgrade `enapter` to `0.17.0`
- Add git-cliff configuration and initial changelog
- *(makefile)* Update bump-version to generate changelog using git-cliff
- *(release)* Bump version to 0.9.0
## [0.8.3] - 2026-03-02

### 🚀 Features

- *(mcp)* Client: proxy x-enapter-auth-user

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version to 0.8.3
## [0.8.2] - 2026-02-17

### ⚙️ Miscellaneous Tasks

- *(mcp)* Models: make type aliases implicit to enable dereference
- *(release)* Bump version to 0.8.2
## [0.8.1] - 2026-02-17

### 🚜 Refactor

- Replace Enums with Literals using PEP 695 type aliases to fix Claude Desktop compatibility

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version to 0.8.1

### ◀️ Revert

- Mcp: server: `read_blueprint`: rename `section` to `blueprint_section`
## [0.8.0] - 2026-02-13

### 🚀 Features

- Integrate with sentry

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version to 0.8.0
## [0.7.2] - 2026-02-13

### 🚀 Features

- *(mcp)* Server: require JWT signing key if OAuth proxy is enabled

### 🚜 Refactor

- *(mcp)* Server: `read_blueprint`: rename `section` to `blueprint_section`

### ⚙️ Miscellaneous Tasks

- *(makefile)* Extend `bump-version` to make git commit and tag
- *(release)* Bump version to 0.7.2
## [0.7.1] - 2026-02-12

### ⚙️ Miscellaneous Tasks

- *(setup)* Fix typo
- *(release)* Bump version
## [0.7.0] - 2026-02-12

### 🚀 Features

- *(mcp)* Server: add read-only annotation for tools
- *(mcp)* Server: add optional jwt store

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version
## [0.6.2] - 2026-02-12

### 🎨 Styling

- *(mcp)* Server: customize logo

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version
## [0.6.1] - 2026-02-10

### ⚙️ Miscellaneous Tasks

- *(cli)* Serve: disable oauth proxy by default
- *(release)* Bump version
## [0.6.0] - 2026-02-10

### 🚀 Features

- *(mcp)* Introduce server config
- *(mcp)* Add logging configuration
- *(mcp)* Server: optionally support enapter api authentication by username
- *(mcp)* Implement oauth proxy auth

### 🚜 Refactor

- *(pipfile)* Remove `ollmcp`
- *(mcp)* Server: use stateless http
- *(mcp)* Server: reuse enapter http api client

### 📚 Documentation

- Update README to reflect current implementation (#2)

### 🧪 Testing

- Add unit tests for data models with factory methods (#3)

### ⚙️ Miscellaneous Tasks

- *(setup)* Add `httpx` to dependencies
- *(release)* Bump version

### ◀️ Revert

- Server: print version on start
## [0.5.0] - 2026-02-03

### 🚀 Features

- *(models)* Fix enum type annotation
- *(models)* Handle `alerts` data type
- *(server)* Implement pagination for blueprint sections
- *(server)* Add pagination for site and device search
- *(models)* Expose `display_name` from blueprint
- *(server)* Print version on start

### 🚜 Refactor

- *(server)* Rename `read_blueprint_section` to `read_blueprint`

### 📚 Documentation

- *(server)* Better instructions

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version
## [0.4.0] - 2026-02-02

### 🚀 Features

- *(server)* Introduce device blueprint

### 🧪 Testing

- *(server)* Remove latest telemetry tool

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version
## [0.3.2] - 2026-01-30

### 🚀 Features

- *(cli)* Add `version` command
- *(server)* Device context: manifest: handle empty telemetry and properties

### ⚙️ Miscellaneous Tasks

- Run only on python 3.14
- *(setup)* Fix enapter-sdk version
- *(release)* Bump version
- *(release)* Bump version
## [0.3.0] - 2026-01-30

### 🚀 Features

- *(server)* Introduce site context
- *(server)* Introduce device context
- *(server)* Add timestamps to device and site contexts
- *(server)* Historical telemetry: set default granularity to 1h
- *(cli)* Call_tool: jsonify structured content
- *(models)* Describe device manifest

### 📚 Documentation

- *(server)* Better docstrings
- *(server)* Better instructions for historical telemetry

### 🎨 Styling

- *(server)* Formatting

### ⚙️ Miscellaneous Tasks

- *(release)* Bump version
## [0.2.1] - 2026-01-20

### 🚀 Features

- *(cli)* Add `call_tool` command

### 📚 Documentation

- *(readme)* Update docker image version

### ⚙️ Miscellaneous Tasks

- *(setup)* Pin enapter sdk version
- *(release)* Bump version
## [0.2.0] - 2026-01-20

### 🚀 Features

- *(mcp)* Add models
- *(mcp)* Server: add graceful shutdown timeout
- *(mcp)* Server: support historical telemetry
- *(cli)* Add `list_tools` command
- *(mcp)* Add server metadata

### 🚜 Refactor

- *(mcp)* Server: split tools into smaller ones
- *(mcp)* Server: move tool names and descriptions around
- *(mcp)* Move models to a separate package

### 📚 Documentation

- Initial plan
- Add comprehensive README.md
- Denser readme
- *(makefile)* Fix `DOCKER_IMAGE_TAG` usage
- *(dockerfile)* Configure server to listen on all interfaces by default

### ⚙️ Miscellaneous Tasks

- Merge pull request #1 from Enapter/copilot/create-readme-file
- *(.gitignore)* Add `.gemini`
- Pass task group to mcp server
- *(release)* Bump version
## [0.1.0] - 2026-01-19

### ⚙️ Miscellaneous Tasks

- Init
