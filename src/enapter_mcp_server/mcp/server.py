import asyncio
import datetime
import urllib.parse

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

INSTRUCTIONS = """This MCP server exposes the Enapter API for managing energy systems.

## Example Workflows

### 1. Diagnostic Troubleshooting

**Goal**: Investigate a specific device failure or alert.

- Identify the device using `search_devices(view="full")` to see `active_alerts`.
- Cross-reference alerts with `read_blueprint(section="alerts")` for their definitions.
- Use `search_command_executions` to audit actions recently taken.

### 2. Historical Analysis & Performance Yield

**Goal**: Analyze performance trends (e.g., hydrogen yield, energy storage).

- Find the correct metric name via `read_blueprint(section="telemetry")`.
- Fetch the data with `get_historical_telemetry`.

## Usage Tips

- **Filtering**: Parameters ending in `_regexp` (e.g., `name_regexp`) accept Python-style regular expressions.
"""


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
        fastmcp_server = fastmcp.FastMCP(
            name="Enapter MCP Server",
            instructions=INSTRUCTIONS,
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
        ]
        for tool, title in read_only_tools:
            fastmcp_server.tool(
                tool,
                annotations=mcp.types.ToolAnnotations(
                    readOnlyHint=True,
                    title=title,
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
        """Search among all sites to which the authenticated user has access."""
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

    async def search_devices(
        self,
        device_id: str | None = None,
        site_id: str | None = None,
        type: models.DeviceType | None = None,
        name_regexp: str = ".*",
        connectivity_status: models.ConnectivityStatus | None = None,
        view: models.DeviceView = "basic",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Device]:
        """Search among all devices to which the authenticated user has access.

        The `full` view provides `properties` and `active_alerts` but requires
        `site_id` or `device_id` to keep the amount of data manageable.
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
        )
        devices = await self._app.search_devices(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
            view=domain.DeviceView(view.lower()),
        )
        return [models.Device.from_domain(d) for d in devices]

    async def read_blueprint(
        self,
        device_id: str,
        section: models.BlueprintSection,
        name_regexp: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[
        models.PropertyDeclaration
        | models.TelemetryAttributeDeclaration
        | models.AlertDeclaration
        | models.CommandDeclaration
    ]:
        """Read a specific section of the device blueprint."""
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
            models.PropertyDeclaration
            | models.TelemetryAttributeDeclaration
            | models.AlertDeclaration
            | models.CommandDeclaration
        ] = []

        for d in declarations:
            if isinstance(d, domain.PropertyDeclaration):
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
        view: models.CommandExecutionView = "basic",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.CommandExecution]:
        """Search the history of command executions.

        The `full` view provides `arguments` and and `response_payload` but
        requires `device_id` to keep the amount of data manageable.
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
        )
        executions = await self._app.search_command_executions(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
            view=domain.CommandExecutionView(view.lower()),
        )
        return [models.CommandExecution.from_domain(e) for e in executions]

    async def get_historical_telemetry(
        self,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int = 60 * 60,
        aggregation: models.HistoricalTelemetryAggregation = "auto",
    ) -> models.HistoricalTelemetry:
        """Retrieve aggregated telemetry data.

        Most devices send telemetry data once per second. To reduce the amount
        of data transferred, the `granularity` parameter can be used to
        aggregate data over a specified interval (in seconds). For example, a
        granularity of 3600 seconds (1 hour) will return hourly averages of the
        telemetry data.

        The `aggregation` parameter controls how datapoints within a bucket
        are combined. `auto` picks a sensible per-attribute default.
        """
        auth = await self._get_auth_config()
        telemetry = await self._app.get_historical_telemetry(
            auth=auth,
            device_id=device_id,
            attributes=attributes,
            time_from=time_from,
            time_to=time_to,
            granularity=granularity,
            aggregation=enapter.http.api.telemetry.Aggregation(aggregation.upper()),
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
