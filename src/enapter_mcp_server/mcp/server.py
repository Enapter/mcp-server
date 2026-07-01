import asyncio
import datetime
import urllib.parse
from typing import Any

import enapter
import fastmcp
import fastmcp.server.auth.providers.introspection
import httpx
import key_value.aio.protocols
import key_value.aio.stores.disk
import key_value.aio.stores.memory
import mcp
import starlette

from enapter_mcp_server import __version__, core, domain

from . import models
from .server_config import ServerConfig


class Server(enapter.async_.Routine):

    def __init__(
        self,
        app: core.ApplicationServer,
        config: ServerConfig,
        task_group: asyncio.TaskGroup | None = None,
    ) -> None:
        super().__init__(task_group=task_group)
        self._app = app
        self._config = config

    async def _run(self) -> None:
        icon = (
            mcp.types.Icon(src=self._config.logo_url)
            if self._config.logo_url is not None
            else None
        )
        auth_provider = self._select_auth_provider()
        # NOTE: Instructions are treated as metadata by some clients (e.g.,
        # Claude Desktop) and are not used to guide the LLM's behavior. We
        # provide instructions directly in the tool docstrings instead.
        instructions = None
        fastmcp_server = fastmcp.FastMCP(
            name="Enapter MCP Server",
            instructions=instructions,
            version=__version__,
            website_url="https://github.com/Enapter/mcp-server",
            icons=[icon] if icon is not None else [],
            auth=auth_provider,
        )
        self._register_tools(fastmcp_server)
        await fastmcp_server.run_async(
            transport="streamable-http",
            show_banner=False,
            host=self._config.host,
            port=self._config.port,
            uvicorn_config={"timeout_graceful_shutdown": 5.0},
            middleware=self._new_middleware(),
            stateless_http=True,
        )

    def _select_auth_provider(self) -> fastmcp.server.auth.AuthProvider | None:
        if self._config.oauth_proxy is None:
            return None
        if self._config.oauth_proxy.jwt_signing_key is None:
            raise ValueError("jwt_signing_key must be set when oauth_proxy is enabled")
        token_verifier = (
            fastmcp.server.auth.providers.introspection.IntrospectionTokenVerifier(
                introspection_url=self._config.oauth_proxy.introspection_endpoint_url,
                client_id=self._config.oauth_proxy.client_id,
                client_secret=self._config.oauth_proxy.client_secret,
                required_scopes=self._config.oauth_proxy.required_scopes,
            )
        )
        jwt_store = self._select_jwt_store()
        return fastmcp.server.auth.OAuthProxy(
            upstream_authorization_endpoint=self._config.oauth_proxy.authorization_endpoint_url,
            upstream_token_endpoint=self._config.oauth_proxy.token_endpoint_url,
            upstream_client_id=self._config.oauth_proxy.client_id,
            upstream_client_secret=self._config.oauth_proxy.client_secret,
            token_verifier=token_verifier,
            base_url=self._config.oauth_proxy.protected_resource_url,
            forward_pkce=self._config.oauth_proxy.forward_pkce,
            client_storage=jwt_store,
            jwt_signing_key=self._config.oauth_proxy.jwt_signing_key,
        )

    def _select_jwt_store(self) -> key_value.aio.protocols.AsyncKeyValue:
        assert self._config.oauth_proxy is not None
        if self._config.oauth_proxy.jwt_store_url is None:
            return key_value.aio.stores.memory.MemoryStore()
        jwt_store_url = urllib.parse.urlparse(self._config.oauth_proxy.jwt_store_url)
        match jwt_store_url.scheme:
            case "memory":
                return key_value.aio.stores.memory.MemoryStore()
            case "disk":
                # FIXME: DiskStore is vulnerable to pickle deserialization
                # exploits (CVE-2025-69872).
                return key_value.aio.stores.disk.DiskStore(directory=jwt_store_url.path)
            case _:
                raise NotImplementedError(f"{jwt_store_url.scheme}")

    def _register_tools(self, fastmcp_server: fastmcp.FastMCP) -> None:
        read_only_tools: list[tuple[mcp.types.AnyFunction, str]] = [
            (self.search_sites, "Search Sites"),
            (self.search_devices, "Search Devices"),
            (self.search_command_executions, "Search Command Executions"),
            (self.read_blueprint, "Read Blueprint"),
            (self.get_historical_telemetry, "Get Historical Telemetry"),
            (self.search_rules, "Search Rules"),
            (self.read_rule, "Read Rule"),
        ]
        for tool, title in read_only_tools:
            fastmcp_server.tool(
                tool,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=True,
                    title=title,
                ),
            )

        if self._config.command_execution_enabled:
            fastmcp_server.tool(
                self.execute_command,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=False,
                    destructiveHint=True,
                    title="Execute Command",
                ),
            )

        if self._config.rule_editing_enabled:
            fastmcp_server.tool(
                self.create_rule,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=False,
                    destructiveHint=True,
                    title="Create Rule",
                ),
            )
            fastmcp_server.tool(
                self.edit_rule,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=False,
                    destructiveHint=True,
                    title="Edit Rule",
                ),
            )
            fastmcp_server.tool(
                self.delete_rule,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=False,
                    destructiveHint=True,
                    title="Delete Rule",
                ),
            )

    def _new_middleware(self) -> list[starlette.middleware.Middleware]:
        middleware = []
        if self._config.cors_allow_origins is not None:
            middleware.append(
                self._new_cors_middleware(self._config.cors_allow_origins)
            )
        return middleware

    def _new_cors_middleware(
        self, allow_origins: list[str]
    ) -> starlette.middleware.Middleware:
        return starlette.middleware.Middleware(
            starlette.middleware.cors.CORSMiddleware,
            allow_origins=allow_origins,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["mcp-protocol-version", "mcp-session-id", "Authorization"],
            expose_headers=["mcp-session-id"],
        )

    async def search_sites(
        self,
        site_id: str | None = None,
        name_regexp: str = ".*",
        timezone_regexp: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Site]:
        """Search among energy system sites accessible to the authenticated user.

        This tool is typically the first step to discover a `site_id`, which is often required by other tools to scope queries to a specific location.

        Tips:
        - Both `name_regexp` and `timezone_regexp` accept Python-style regular expressions.

        Related tools:
        - `search_devices`: Pass the discovered `site_id` to find devices located at this site.
        - `search_rules`: Pass the discovered `site_id` to list the automation rules running on the site.
        - `search_command_executions`: Pass the discovered `site_id` to audit commands executed across the entire site.
        """
        auth = await self._get_auth_config()
        query = core.SiteSearchQuery(
            site_id=site_id,
            name_regexp=name_regexp,
            timezone_regexp=timezone_regexp,
        )
        sites = await self._app.search_sites(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
        )
        return [models.Site.from_domain(s) for s in sites]

    async def search_rules(
        self,
        site_id: str,
        rule_id: str | None = None,
        slug_regexp: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Rule]:
        """Search for automation rules running on a specific site.

        This tool allows you to list and filter the Rule Engine rules configured on a site.

        Tips:
        - `slug_regexp` accepts a Python-style regular expression.

        Related tools:
        - `read_rule`: Pass the discovered `rule_id` and `site_id` to read the actual Lua script code of the rule.
        """
        auth = await self._get_auth_config()
        query = core.RuleSearchQuery(
            site_id=site_id,
            rule_id=rule_id,
            slug_regexp=slug_regexp,
        )
        rules = await self._app.search_rules(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
        )
        return [models.Rule.from_domain(r) for r in rules]

    async def read_rule(
        self,
        site_id: str,
        rule_id: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> list[str]:
        """Read the Lua script code for a specific automation rule.

        This tool returns the source code of a rule running on the Enapter Rule Engine, returned as a list of strings (lines of code).

        Tips:
        - Use `offset` and `limit` to paginate through the code if the rule's `lines_count` is very large, preventing context window overflow.
        """
        auth = await self._get_auth_config()
        return await self._app.read_rule(
            auth=auth,
            site_id=site_id,
            rule_id=rule_id,
            offset=offset,
            limit=limit,
        )

    async def search_devices(
        self,
        device_id: str | None = None,
        site_id: str | None = None,
        type: models.DeviceType | None = None,
        name_regexp: str = ".*",
        connectivity_status: models.ConnectivityStatus | None = None,
        has_active_alerts: bool | None = None,
        view: models.DeviceView = "basic",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Device]:
        """Search for energy system devices.

        This tool is the primary entry point for discovering devices, checking their connectivity, and finding active alerts during diagnostic troubleshooting.

        Tips:
        - Use `has_active_alerts=True` to quickly find devices that require attention.
        - The default `view="basic"` returns summary information. To retrieve the `active_alerts` list and device `properties`, use `view="full"` (requires specifying either `site_id` or `device_id`).
        - `name_regexp` accepts a Python-style regular expression.
        - Devices sharing the same `blueprint_id` have identical manifests, so `read_blueprint` need only be called once per unique `blueprint_id`. Reuse the result for every device with a matching `blueprint_id` to avoid redundant calls.

        Related tools:
        - `read_blueprint`: Pass the device `id` to read its blueprint and discover its telemetry attributes, commands, alerts, and properties.
        - `get_historical_telemetry`: Pass the device `id` to retrieve historical time-series data (e.g., hydrogen yield, energy storage).
        - `search_command_executions`: Pass the device `id` to audit actions recently taken on this device.
        """
        auth = await self._get_auth_config()
        device_type = domain.DeviceType(type.lower()) if type is not None else None
        query = core.DeviceSearchQuery(
            device_id=device_id,
            site_id=site_id,
            device_type=device_type,
            name_regexp=name_regexp,
            connectivity_status=(
                domain.ConnectivityStatus(connectivity_status.lower())
                if connectivity_status is not None
                else None
            ),
            has_active_alerts=has_active_alerts,
        )
        views = await self._app.search_devices(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
            view=domain.DeviceViewType(view.lower()),
        )
        return [models.Device.from_view(v) for v in views]

    async def read_blueprint(
        self,
        device_id: str,
        section: models.BlueprintSection,
        name_regexp: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[
        str
        | models.PropertyDeclaration
        | models.TelemetryAttributeDeclaration
        | models.AlertDeclaration
        | models.CommandDeclaration
    ]:
        """Read the blueprint for a specific device.

        This tool retrieves the schema defining the capabilities of a device, divided into sections: 'telemetry', 'alerts', 'commands', 'properties', and 'implements'.

        Tips:
        - Use `section="alerts"` to get details about specific alerts.
        - Use `section="telemetry"` to discover the exact names and metadata of telemetry attributes.
        - Use `section="commands"` to see which actions can be executed on the device.
        - Use `section="implements"` to list the standardized profiles that the device implements.
        - `name_regexp` accepts a Python-style regular expression.

        Related tools:
        - `get_historical_telemetry`: Pass the telemetry attributes discovered here to retrieve historical time-series data.
        - `search_command_executions`: Use the commands discovered here to audit their past executions.

        See also:
        - https://github.com/Enapter/profiles — documentation on the standardized profiles that blueprints implement.
        """
        auth = await self._get_auth_config()
        declarations = await self._app.read_blueprint(
            auth=auth,
            device_id=device_id,
            section=domain.BlueprintSection(section),
            name_regexp=name_regexp,
            offset=offset,
            limit=limit,
        )

        models_list: list[
            str
            | models.PropertyDeclaration
            | models.TelemetryAttributeDeclaration
            | models.AlertDeclaration
            | models.CommandDeclaration
        ] = []

        for d in declarations:
            if isinstance(d, str):
                models_list.append(d)
            elif isinstance(d, domain.PropertyDeclaration):
                models_list.append(models.PropertyDeclaration.from_domain(d))
            elif isinstance(d, domain.TelemetryAttributeDeclaration):
                models_list.append(models.TelemetryAttributeDeclaration.from_domain(d))
            elif isinstance(d, domain.AlertDeclaration):
                models_list.append(models.AlertDeclaration.from_domain(d))
            elif isinstance(d, domain.CommandDeclaration):
                models_list.append(models.CommandDeclaration.from_domain(d))
            else:
                raise NotImplementedError(type(d))

        return models_list

    async def search_command_executions(
        self,
        device_id: str | None = None,
        site_id: str | None = None,
        command_name_regexp: str = ".*",
        state: models.CommandExecutionState | None = None,
        created_at_gte: datetime.datetime | None = None,
        created_at_lt: datetime.datetime | None = None,
        view: models.CommandExecutionView = "basic",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.CommandExecution]:
        """Search the history of commands executed on devices.

        This tool helps audit recent actions taken on a device, whether to verify successful execution, check for failures (`state="error"`), or see if a command was misused.

        Tips:
        - The default `view="basic"` returns execution status and timestamps.
        - Use `view="full"` to see the actual `arguments` sent and the `response_payload` received.
        - `view="full"` requires specifying a `device_id`.
        - `command_name_regexp` accepts a Python-style regular expression.
        - `created_at_gte` and `created_at_lt` can be used to filter by time.
        """
        auth = await self._get_auth_config()
        query = core.CommandExecutionSearchQuery(
            device_id=device_id,
            site_id=site_id,
            command_name_regexp=command_name_regexp,
            state=(
                domain.CommandExecutionState(state.lower())
                if state is not None
                else None
            ),
            created_at_gte=created_at_gte,
            created_at_lt=created_at_lt,
        )
        executions = await self._app.search_command_executions(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
            view=domain.CommandExecutionView(view.lower()),
        )
        return [models.CommandExecution.from_domain(e) for e in executions]

    async def execute_command(
        self,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None = None,
        human_confirmed_this_action: bool = False,
    ) -> models.CommandExecution:
        """Execute a command on a specific device and return its outcome.

        This tool performs a real-world action on physical energy hardware. It is destructive: use it only when acting is intended.

        The `state` field of the returned `CommandExecution` communicates the outcome. If the underlying call fails to submit (e.g. insufficient role or a network error), the exception propagates.

        Some commands declare a `confirmation` block because they are consequential. Before executing such a command you MUST obtain a human's explicit approval through a structured form: present the device, the command, and the confirmation's `title`/`description` as a prompt with discrete choices whose options include exactly one explicit "approve" choice, then wait for the human to select it. Approval counts ONLY when the returned answer exactly matches that approve option. Never infer approval from free-text conversation ("yes", "maybe", "sure", "I think so", silence, or any other reply), and never accept a typed/free-text answer even when the form permits one instead of a selection — if the response is anything other than an exact selection of the approve option, re-present the form or do not execute. Only after such a form approval may you set `human_confirmed_this_action=True` to attest it. For commands without a `confirmation` block, the flag is ignored.

        Related tools:
        - `read_blueprint`: Use `section="commands"` to discover a device's commands, arguments, and `confirmation` blocks.
        - `search_command_executions`: Audit past executions or recover the outcome of a cancelled/timed-out call.
        """
        auth = await self._get_auth_config()
        execution = await self._app.execute_command(
            auth=auth,
            device_id=device_id,
            command_name=command_name,
            arguments=arguments,
            human_confirmed_this_action=human_confirmed_this_action,
        )
        return models.CommandExecution.from_domain(execution)

    async def create_rule(
        self,
        site_id: str,
        slug: str,
        script_code: str,
    ) -> models.Rule:
        """Create a disabled MCP-managed automation rule on a site.

        This tool creates a new rule that is always disabled and uses runtime version v3.
        The slug must start with the MCP-managed prefix `mcp-`. The creator does not
        enable the rule; a human must review and enable it in the Enapter UI.

        Related tools:
        - `search_rules`: List rules on the site including the newly created one.
        - `read_rule`: Read the full script of the newly created rule.
        - `edit_rule`: Modify the rule's script via content-match editing.
        - `delete_rule`: Remove the rule.
        """
        auth = await self._get_auth_config()
        rule = await self._app.create_rule(
            auth=auth,
            site_id=site_id,
            slug=slug,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code=script_code,
            ),
            disabled=True,
        )
        return models.Rule.from_domain(rule)

    async def edit_rule(
        self,
        site_id: str,
        rule_id: str,
        old_string: str,
        new_string: str,
    ) -> models.Rule:
        """Apply a content-match edit to a disabled MCP-managed rule's script.

        This tool replaces exactly one occurrence of `old_string` with `new_string`
        in the rule's current Lua script. The rule must be disabled, its slug must
        start with `mcp-`, and it must use runtime version v3.

        `old_string` must be non-empty, must appear exactly once in the current
        script, and must differ from `new_string`.

        The updated `Rule` object is returned. Use `read_rule` if you need to
        inspect the resulting source code.

        Related tools:
        - `read_rule`: Inspect the current script before crafting an edit.
        - `create_rule`: Create a new MCP-managed rule.
        - `delete_rule`: Remove the rule.
        """
        auth = await self._get_auth_config()
        rule = await self._app.edit_rule(
            auth=auth,
            site_id=site_id,
            rule_id=rule_id,
            old_string=old_string,
            new_string=new_string,
        )
        return models.Rule.from_domain(rule)

    async def delete_rule(
        self,
        site_id: str,
        rule_id: str,
    ) -> None:
        """Delete a disabled MCP-managed automation rule.

        The rule must be disabled and its slug must start with `mcp-`. The tool
        returns no result; confirm deletion via `search_rules`.

        Related tools:
        - `search_rules`: Verify the rule no longer exists after deletion.
        - `create_rule`: Re-create the rule if needed.
        """
        auth = await self._get_auth_config()
        await self._app.delete_rule(
            auth=auth,
            site_id=site_id,
            rule_id=rule_id,
        )

    async def get_historical_telemetry(
        self,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        aggregation: models.AggregationFunction,
        granularity: int = 60 * 60,
    ) -> models.HistoricalTelemetry:
        """Retrieve aggregated historical time-series telemetry for a specific device.

        This tool is useful for performance analysis, yield calculation, and historical trending.

        The data is divided into time buckets of `granularity` seconds. Each returned timestamp marks the start of a bucket, and its values are the result of applying the `aggregation` function to all data points within that bucket.

        Telemetry attributes the user cannot read (per their `authorized_role`) are absent from the result.

        Tips:
        - Use `read_blueprint` to discover exact telemetry attribute names for the `attributes` parameter.
        - Choose an `aggregation` function suitable for the attribute's data type. For example, `last` works for booleans and strings, while `min`, `max`, and `avg` work for numerics.
        """
        auth = await self._get_auth_config()
        telemetry = await self._app.get_historical_telemetry(
            auth=auth,
            device_id=device_id,
            attributes=attributes,
            time_from=time_from,
            time_to=time_to,
            granularity=granularity,
            aggregation=domain.AggregationFunction(aggregation),
        )
        return models.HistoricalTelemetry.from_domain(telemetry)

    async def _get_auth_config(self) -> core.AuthConfig:
        if self._config.oauth_proxy is None:
            headers = fastmcp.server.dependencies.get_http_headers()
            return core.AuthConfig(
                token=headers.get("x-enapter-auth-token"),
                user=headers.get("x-enapter-auth-user"),
            )

        access_token = fastmcp.server.dependencies.get_access_token()
        assert access_token is not None
        async with httpx.AsyncClient() as client:
            assert self._config.oauth_proxy is not None
            response = await client.get(
                self._config.oauth_proxy.user_info_endpoint_url,
                headers={"Authorization": f"Bearer {access_token.token}"},
            )
            response.raise_for_status()
            user_info = response.json()
            return core.AuthConfig(user=user_info["guid"])
