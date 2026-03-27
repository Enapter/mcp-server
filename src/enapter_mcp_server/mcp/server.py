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

Workflow:
- Search: Find sites (`search_sites`) or devices (`search_devices`) to obtain IDs.
- Details: Use `search_sites` or `search_devices(view="FULL")` for comprehensive views.
- Deep Dive: Explore device manifests with `read_blueprint_manifest` and fetch historical data with `get_historical_telemetry`.
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
            (self.read_blueprint_manifest, "Read Blueprint Manifest"),
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
        name_pattern: str = ".*",
        timezone_pattern: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Site]:
        """Search among all sites to which the authenticated user has access."""
        auth = await self._get_auth_config()
        query = core.SiteSearchQuery(
            name_pattern=name_pattern,
            timezone_pattern=timezone_pattern,
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
        site_id: str | None = None,
        type: models.DeviceType | None = None,
        name_pattern: str = ".*",
        view: models.DeviceView = "BASIC",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Device]:
        """Search among all devices in a site with BASIC or FULL views."""
        auth = await self._get_auth_config()
        device_type = domain.DeviceType(type) if type is not None else None
        query = core.DeviceSearchQuery(
            site_id=site_id,
            device_type=device_type,
            name_pattern=name_pattern,
        )
        devices = await self._app.search_devices(
            auth=auth,
            query=query,
            offset=offset,
            limit=limit,
            view=domain.DeviceView(view),
        )
        return [models.Device.from_domain(d) for d in devices]

    async def read_blueprint_manifest(
        self,
        device_id: str,
        section: models.BlueprintManifestSection,
        name_pattern: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[
        models.PropertyDeclaration
        | models.TelemetryAttributeDeclaration
        | models.AlertDeclaration
        | models.CommandDeclaration
    ]:
        """Read a specific section of the device blueprint manifest."""
        auth = await self._get_auth_config()
        declarations = await self._app.read_blueprint_manifest(
            auth=auth,
            device_id=device_id,
            section=domain.BlueprintManifestSection(section),
            name_pattern=name_pattern,
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

    async def get_historical_telemetry(
        self,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int = 60 * 60,
    ) -> models.HistoricalTelemetry:
        """Get historical telemetry by device ID, attributes, time range, and granularity.

        Most devices send telemetry data once per second. To reduce the amount
        of data transferred, the `granularity` parameter can be used to
        aggregate data over a specified interval (in seconds). For example, a
        granularity of 3600 seconds (1 hour) will return hourly averages of the
        telemetry data.
        """
        auth = await self._get_auth_config()
        telemetry = await self._app.get_historical_telemetry(
            auth=auth,
            device_id=device_id,
            attributes=attributes,
            time_from=time_from,
            time_to=time_to,
            granularity=granularity,
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
