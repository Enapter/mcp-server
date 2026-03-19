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

from enapter_mcp_server import __version__, core, domain

from . import models
from .server_config import ServerConfig

INSTRUCTIONS = """This MCP server exposes the Enapter HTTP API, enabling management of energy systems.

Workflow:

- Start by searching for sites or devices if IDs are not provided.
- Use `get_site_context` or `get_device_context` to get a comprehensive view.
- Drill down into specific blueprint sections or historical data as needed.
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
        read_only_tools: list[mcp.types.AnyFunction] = [
            self.search_sites,
            self.get_site_context,
            self.search_devices,
            self.get_device_context,
            self.read_blueprint,
            self.get_historical_telemetry,
        ]
        for tool in read_only_tools:
            fastmcp_server.tool(
                tool, annotations=mcp.types.ToolAnnotations(readOnlyHint=True)
            )

    async def search_sites(
        self,
        name_pattern: str = ".*",
        timezone_pattern: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Site]:
        """Search among all sites to which the authenticated user has access.

        Args:
            name_pattern: A regular expression pattern to match site names.
            timezone_pattern: A regular expression pattern to match site timezones.
            offset: The offset of the first site to return.
            limit: The maximum number of sites to return.

        Returns:
            A list of sites matching the specified patterns sorted by site ID.

        Related tools:
            get_site_context: Get detailed context about a specific site.
            search_devices: Search for devices within a specific site.
        """
        auth = await self._get_auth_config()
        sites = await self._app.search_sites(
            auth=auth,
            name_pattern=name_pattern,
            timezone_pattern=timezone_pattern,
            offset=offset,
            limit=limit,
        )
        return [models.Site.from_domain(s) for s in sites]

    async def get_site_context(self, site_id: str) -> models.SiteContext:
        """Get site context by site ID.

        Args:
            site_id: The ID of the site.

        Returns:
            The site context including site details and device statistics.

        Related tools:
            search_devices: Search for devices within a specific site.
        """
        auth = await self._get_auth_config()
        context = await self._app.get_site_context(auth=auth, site_id=site_id)
        return models.SiteContext.from_domain(context)

    async def search_devices(
        self,
        site_id: str | None = None,
        type: models.DeviceType | None = None,
        name_pattern: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[models.Device]:
        """Search among all devices in a site.

        Args:
            site_id: The ID of the site.
            type: The type of the device to filter by.
            name_pattern: A regular expression pattern to match device names.
            offset: The offset of the first device to return.
            limit: The maximum number of devices to return.

        Returns:
            A list of devices matching the specified criteria sorted by device ID.

        Related tools:
            get_device_context: Get detailed context about a specific device.
            read_blueprint_section: Read specific sections of a device's blueprint.
            get_historical_telemetry: Get historical telemetry data of a device.
        """
        auth = await self._get_auth_config()
        device_type = domain.DeviceType(type) if type is not None else None
        devices = await self._app.search_devices(
            auth=auth,
            site_id=site_id,
            device_type=device_type,
            name_pattern=name_pattern,
            offset=offset,
            limit=limit,
        )
        return [models.Device.from_domain(d) for d in devices]

    async def get_device_context(self, device_id: str) -> models.DeviceContext:
        """Get device context by device ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The device context including connectivity status, properties,
            latest telemetry, and blueprint summary.

        Related tools:
            read_blueprint_section: Read specific sections of the device's blueprint.
            get_historical_telemetry: Get historical telemetry data of the device.
        """
        auth = await self._get_auth_config()
        context = await self._app.get_device_context(auth=auth, device_id=device_id)
        return models.DeviceContext.from_domain(context)

    async def read_blueprint(
        self,
        device_id: str,
        section: models.BlueprintSection,
        name_pattern: str = ".*",
        offset: int = 0,
        limit: int = 20,
    ) -> list[
        models.PropertyDeclaration
        | models.TelemetryAttributeDeclaration
        | models.AlertDeclaration
    ]:
        """Read a specific section of the device blueprint.

        A blueprint can contain hundreds of declarations, therefore this tool
        supports pagination via `offset` and `limit` parameters.

        Args:
            device_id: The ID of the device.
            section: The section of the blueprint to read.
            name_pattern: A regular expression pattern to match declaration names.
            offset: The offset of the first declaration to return.
            limit: The maximum number of declarations to return.

        Returns:
            A list of declarations in the specified blueprint section.
        """
        auth = await self._get_auth_config()
        declarations = await self._app.read_blueprint(
            auth=auth,
            device_id=device_id,
            section=domain.BlueprintSection(section),
            name_pattern=name_pattern,
            offset=offset,
            limit=limit,
        )

        models_list: list[
            models.PropertyDeclaration
            | models.TelemetryAttributeDeclaration
            | models.AlertDeclaration
        ] = []

        for d in declarations:
            if isinstance(d, domain.PropertyDeclaration):
                models_list.append(models.PropertyDeclaration.from_domain(d))
            elif isinstance(d, domain.TelemetryAttributeDeclaration):
                models_list.append(models.TelemetryAttributeDeclaration.from_domain(d))
            elif isinstance(d, domain.AlertDeclaration):
                models_list.append(models.AlertDeclaration.from_domain(d))
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

        Args:
            device_id: The ID of the device.
            attributes: A list of telemetry attributes to retrieve.
            time_from: The start time of the telemetry data.
            time_to: The end time of the telemetry data.
            granularity: The granularity of the telemetry data in seconds.

        Returns:
            The historical telemetry data for the specified device and attributes.

        Related tools:
            read_blueprint_section: Read the telemetry attributes declared in
                the device's blueprint.
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
