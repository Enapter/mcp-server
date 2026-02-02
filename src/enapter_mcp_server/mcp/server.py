import asyncio
import datetime
import re
from typing import AsyncContextManager

import enapter
import fastmcp

from enapter_mcp_server import __version__

from . import models


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
            name="Enapter MCP Server",
            instructions="An MCP server exposing Enapter HTTP API functionality.",
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
        mcp.tool(self.get_blueprint)
        mcp.tool(self.get_device_latest_telemetry)
        mcp.tool(self.get_historical_telemetry)

    async def search_sites(
        self, name_pattern: str = ".*", timezone_pattern: str = ".*"
    ) -> list[models.Site]:
        """Search among all sites to which the authenticated user has access.

        Args:
            name_pattern: A regular expression pattern to match site names.
            timezone_pattern: A regular expression pattern to match site timezones.

        Returns:
            A list of sites matching the specified patterns.
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
                return sites

    async def get_site_context(self, site_id: str) -> models.SiteContext:
        """Get site context by site ID.

        Args:
            site_id: The ID of the site.

        Returns:
            The site context including site details and device statistics.
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
        site_id: str,
        type: models.DeviceType | None = None,
        name_pattern: str = ".*",
    ) -> list[models.Device]:
        """Search among all devices in a site.

        Args:
            site_id: The ID of the site.
            type: The type of the device to filter by.
            name_pattern: A regular expression pattern to match device names.

        Returns:
            A list of devices matching the specified criteria.
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
                return devices

    async def get_device_context(self, device_id: str) -> models.DeviceContext:
        """Get device context by device ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The device context including connectivity status, properties,
            and latest telemetry.
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
            )

    async def get_blueprint(self, device_id: str) -> models.Blueprint:
        """Get device blueprint by device ID.

        Args:
            device_id: The ID of the device.

        Returns:
            The device blueprint.
        """
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_manifest=True)
            assert device.manifest is not None
            return models.Blueprint.from_dto(device.manifest)

    async def get_device_latest_telemetry(
        self, device_id: str, attributes: list[str]
    ) -> models.LatestTelemetry:
        """Get device latest telemetry by device ID and attributes.

        Args:
            device_id: The ID of the device.
            attributes: A list of telemetry attributes to retrieve.

        Returns:
            The latest telemetry data for the specified device and attributes.
        """
        async with self._new_http_api_client() as client:
            telemetry = await client.telemetry.latest({device_id: attributes})
            timestamp = max(
                datapoint.timestamp
                for datapoint in telemetry[device_id].values()
                if datapoint is not None
            )
            return models.LatestTelemetry(
                timestamp=timestamp,
                values={
                    attribute: datapoint.value if datapoint is not None else None
                    for attribute, datapoint in telemetry[device_id].items()
                },
            )

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
