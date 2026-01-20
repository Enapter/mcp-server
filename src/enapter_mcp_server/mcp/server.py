import datetime
from typing import Any, AsyncContextManager

import enapter
import fastmcp

from .models import Device, DeviceConnectivityStatus, HistoricalTelemetryData, Site


class Server(enapter.async_.Routine):

    def __init__(
        self,
        host: str,
        port: int,
        enapter_http_api_url: str,
        graceful_shutdown_timeout: float = 5.0,
    ) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._enaper_http_api_url = enapter_http_api_url
        self._graceful_shutdown_timeout = graceful_shutdown_timeout

    async def _run(self) -> None:
        mcp = fastmcp.FastMCP()
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
        mcp.tool(self.list_sites)
        mcp.tool(self.get_site)
        mcp.tool(self.list_site_devices)
        mcp.tool(self.get_device)
        mcp.tool(self.get_device_properties)
        mcp.tool(self.get_device_manifest)
        mcp.tool(self.get_device_connectivity_status)
        mcp.tool(self.get_device_latest_telemetry_data)
        mcp.tool(self.get_device_historical_telemetry_data)

    async def list_sites(self) -> list[Site]:
        "List all sites to which the authenticated user has access."
        async with self._new_http_api_client() as client:
            async with client.sites.list() as stream:
                return [Site.from_domain(site) async for site in stream]

    async def get_site(self, site_id: str) -> Site:
        "Get site by site ID."
        async with self._new_http_api_client() as client:
            site = await client.sites.get(site_id)
            return Site.from_domain(site)

    async def list_site_devices(self, site_id: str) -> list[Device]:
        "List devices by site ID."
        async with self._new_http_api_client() as client:
            async with client.devices.list(site_id=site_id) as stream:
                return [Device.from_domain(device) async for device in stream]

    async def get_device(self, device_id: str) -> Device:
        "Get device by device ID."
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id)
            return Device.from_domain(device)

    async def get_device_properties(self, device_id: str) -> dict[str, Any]:
        "Get device properties by device ID."
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_properties=True)
            assert device.properties is not None
            return device.properties

    async def get_device_manifest(self, device_id: str) -> dict[str, Any]:
        "Get device manifest by device ID."
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_manifest=True)
            assert device.manifest is not None
            return device.manifest

    async def get_device_connectivity_status(
        self, device_id: str
    ) -> DeviceConnectivityStatus:
        "Get device connectivity status by device ID."
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_connectivity=True)
            assert device.connectivity is not None
            return DeviceConnectivityStatus(device.connectivity.status.value)

    async def get_device_latest_telemetry_data(
        self, device_id: str, attributes: list[str]
    ) -> dict[str, Any]:
        "Get device latest telemetry data by device ID and attributes."
        async with self._new_http_api_client() as client:
            telemetry = await client.telemetry.latest({device_id: attributes})
            return {
                attribute: datapoint.value if datapoint is not None else None
                for attribute, datapoint in telemetry[device_id].items()
            }

    async def get_device_historical_telemetry_data(
        self,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int = 60,
    ) -> HistoricalTelemetryData:
        "Get device historical telemetry data by device ID, attributes, time range, and granularity."
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
            return HistoricalTelemetryData(
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
