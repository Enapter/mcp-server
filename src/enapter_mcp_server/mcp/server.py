import asyncio
import datetime
import re
from typing import AsyncContextManager

import enapter
import fastmcp

from enapter_mcp_server import __version__

from . import models

INSTRUCTIONS = """This MCP server exposes the Enapter HTTP API, enabling management of energy systems.

Workflow:

- Start by searching for sites or devices if IDs are not provided.
- Use `get_site_context` or `get_device_context` to get a comprehensive view.
- Drill down into specific blueprint sections or historical data as needed.
"""


class Server(enapter.async_.Routine):

    def __init__(
        self,
        host: str,
        port: int,
        enapter_http_api_url: str,
        graceful_shutdown_timeout: float = 5.0,
        task_group: asyncio.TaskGroup | None = None,
    ) -> None:
        super().__init__(task_group=task_group)
        self._host = host
        self._port = port
        self._enaper_http_api_url = enapter_http_api_url
        self._graceful_shutdown_timeout = graceful_shutdown_timeout

    async def _run(self) -> None:
        mcp = fastmcp.FastMCP(
            name=f"Enapter MCP Server v{__version__}",
            instructions=INSTRUCTIONS,
            version=__version__,
            website_url="https://github.com/Enapter/mcp-server",
        )
        self._register_tools(mcp)
        await mcp.run_async(
            transport="streamable-http",
            show_banner=False,
            host=self._host,
            port=self._port,
            uvicorn_config={
                "timeout_graceful_shutdown": self._graceful_shutdown_timeout
            },
        )

    def _register_tools(self, mcp: fastmcp.FastMCP) -> None:
        mcp.tool(self.search_sites)
        mcp.tool(self.get_site_context)
        mcp.tool(self.search_devices)
        mcp.tool(self.get_device_context)
        mcp.tool(self.read_blueprint)
        mcp.tool(self.get_historical_telemetry)

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
        name_regexp = re.compile(name_pattern)
        timezone_regexp = re.compile(timezone_pattern)
        async with self._new_http_api_client() as client:
            async with client.sites.list() as stream:
                sites = []
                async for site in stream:
                    if name_regexp.search(site.name) and (
                        timezone_regexp.search(site.timezone)
                    ):
                        sites.append(models.Site.from_domain(site))
                sites.sort(key=lambda s: s.id)
                return sites[offset : offset + limit]

    async def get_site_context(self, site_id: str) -> models.SiteContext:
        """Get site context by site ID.

        Args:
            site_id: The ID of the site.

        Returns:
            The site context including site details and device statistics.

        Related tools:
            search_devices: Search for devices within a specific site.
        """
        async with self._new_http_api_client() as client:
            site = await client.sites.get(site_id)
            gateway_id: str | None = None
            gateway_online = False
            devices_total = 0
            devices_online = 0
            async with client.devices.list(
                site_id=site_id, expand_connectivity=True
            ) as stream:
                async for device in stream:
                    assert device.connectivity is not None
                    devices_total += 1
                    device_online = (
                        device.connectivity.status
                        == enapter.http.api.devices.DeviceConnectivityStatus.ONLINE
                    )
                    if device_online:
                        devices_online += 1
                    if device.type == enapter.http.api.devices.DeviceType.GATEWAY:
                        assert gateway_id is None
                        gateway_id = device.id
                        gateway_online = device_online
            return models.SiteContext(
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                site=models.Site.from_domain(site),
                gateway_id=gateway_id,
                gateway_online=gateway_online,
                devices_total=devices_total,
                devices_online=devices_online,
            )

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
        name_regexp = re.compile(name_pattern)
        async with self._new_http_api_client() as client:
            async with client.devices.list(site_id=site_id) as stream:
                devices = []
                async for device in stream:
                    if (type is None or device.type == type) and name_regexp.search(
                        device.name
                    ):
                        devices.append(models.Device.from_domain(device))
                devices.sort(key=lambda d: d.id)
                return devices[offset : offset + limit]

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
        async with self._new_http_api_client() as client:
            device = await client.devices.get(
                device_id,
                expand_manifest=True,
                expand_connectivity=True,
                expand_properties=True,
            )
            assert device.manifest is not None
            assert device.connectivity is not None
            assert device.properties is not None
            latest_telemetry = (
                await client.telemetry.latest(
                    {device_id: list(device.manifest.get("telemetry", {}))}
                )
            )[device_id]
            return models.DeviceContext(
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                device=models.Device.from_domain(device),
                connectivity_status=(
                    models.ConnectivityStatus(device.connectivity.status.value)
                ),
                properties={
                    k: device.properties.get(k)
                    for k in device.manifest.get("properties", {})
                },
                latest_telemetry={
                    k: v.value if v is not None else None
                    for k, v in latest_telemetry.items()
                },
                blueprint_summary=models.BlueprintSummary.from_manifest(
                    device.manifest
                ),
            )

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
        name_regexp = re.compile(name_pattern)
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_manifest=True)
            assert device.manifest is not None
            entities: list[
                models.PropertyDeclaration
                | models.TelemetryAttributeDeclaration
                | models.AlertDeclaration
            ]
            match section:
                case models.BlueprintSection.PROPERTIES:
                    entities = [
                        models.PropertyDeclaration.from_dto(name, dto)
                        for name, dto in device.manifest.get("properties", {}).items()
                    ]
                case models.BlueprintSection.TELEMETRY:
                    entities = [
                        models.TelemetryAttributeDeclaration.from_dto(name, dto)
                        for name, dto in device.manifest.get("telemetry", {}).items()
                    ]
                case models.BlueprintSection.ALERTS:
                    entities = [
                        models.AlertDeclaration.from_dto(name, dto)
                        for name, dto in device.manifest.get("alerts", {}).items()
                    ]
                case _:
                    raise NotImplementedError(section)
            entities = [e for e in entities if name_regexp.search(e.name)]
            entities.sort(key=lambda e: e.name)
            return entities[offset : offset + limit]

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
        async with self._new_http_api_client() as client:
            telemetry = await client.telemetry.wide_timeseries(
                from_=time_from,
                to=time_to,
                granularity=granularity,
                selectors=[
                    enapter.http.api.telemetry.Selector(
                        device=device_id, attributes=attributes
                    )
                ],
            )
            return models.HistoricalTelemetry(
                timestamps=telemetry.timestamps,
                values={
                    column.labels.telemetry: column.values
                    for column in telemetry.columns
                },
            )

    def _new_http_api_client(self) -> AsyncContextManager[enapter.http.api.Client]:
        # FIXME: Client instance gets created for each request.
        headers = fastmcp.server.dependencies.get_http_headers()
        token = headers["x-enapter-auth-token"]
        return enapter.http.api.Client(
            config=enapter.http.api.Config(
                token=token, base_url=self._enaper_http_api_url
            )
        )
