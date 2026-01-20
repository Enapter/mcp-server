from typing import Any, AsyncContextManager

import enapter
import fastmcp

from .models import Device, DeviceConnectivityStatus, Site


class Server(enapter.async_.Routine):

    def __init__(self, host: str, port: int, enapter_http_api_url: str) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._enaper_http_api_url = enapter_http_api_url

    async def _run(self) -> None:
        mcp = fastmcp.FastMCP()
        self._register_tools(mcp)
        await mcp.run_async(
            transport="streamable-http",
            show_banner=False,
            host=self._host,
            port=self._port,
        )

    def _register_tools(self, mcp: fastmcp.FastMCP) -> None:
        mcp.tool(
            self._list_sites,
            name="list_sites",
            description="List all sites to which the authenticated user has access.",
        )
        mcp.tool(
            self._get_site,
            name="get_site",
            description="Get site by site ID.",
        )
        mcp.tool(
            self._list_site_devices,
            name="list_site_devices",
            description="List devices by site ID.",
        )
        mcp.tool(
            self._get_device,
            name="get_device",
            description="Get device by device ID.",
        )
        mcp.tool(
            self._get_device_properties,
            name="get_device_properties",
            description="Get device properties by device ID.",
        )
        mcp.tool(
            self._get_device_manifest,
            name="get_device_manifest",
            description="Get device manifest by device ID.",
        )
        mcp.tool(
            self._get_device_connectivity_status,
            name="get_device_connectivity_status",
            description="Get device connectivity status by device ID.",
        )
        mcp.tool(
            self._get_device_latest_telemetry_data,
            name="get_device_latest_telemetry_data",
            description="Get device latest telemetry data by device ID and attributes.",
        )

    async def _list_sites(self) -> list[Site]:
        async with self._new_http_api_client() as client:
            async with client.sites.list() as stream:
                return [Site.from_domain(site) async for site in stream]

    async def _get_site(self, site_id: str) -> Site:
        async with self._new_http_api_client() as client:
            site = await client.sites.get(site_id)
            return Site.from_domain(site)

    async def _list_site_devices(self, site_id: str) -> list[Device]:
        async with self._new_http_api_client() as client:
            async with client.devices.list(site_id=site_id) as stream:
                return [Device.from_domain(device) async for device in stream]

    async def _get_device(self, device_id: str) -> Device:
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id)
            return Device.from_domain(device)

    async def _get_device_manifest(self, device_id: str) -> dict[str, Any]:
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_manifest=True)
            assert device.manifest is not None
            return device.manifest

    async def _get_device_properties(self, device_id: str) -> dict[str, Any]:
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_properties=True)
            assert device.properties is not None
            return device.properties

    async def _get_device_connectivity_status(
        self, device_id: str
    ) -> DeviceConnectivityStatus:
        async with self._new_http_api_client() as client:
            device = await client.devices.get(device_id, expand_connectivity=True)
            assert device.connectivity is not None
            return DeviceConnectivityStatus(device.connectivity.status.value)

    async def _get_device_latest_telemetry_data(
        self, device_id: str, attributes: list[str]
    ) -> dict[str, Any]:
        async with self._new_http_api_client() as client:
            telemetry = await client.telemetry.latest({device_id: attributes})
            return {
                attribute: datapoint.value if datapoint is not None else None
                for attribute, datapoint in telemetry[device_id].items()
            }

    def _new_http_api_client(self) -> AsyncContextManager[enapter.http.api.Client]:
        # FIXME: Client instance gets created for each request.
        headers = fastmcp.server.dependencies.get_http_headers()
        token = headers["x-enapter-auth-token"]
        return enapter.http.api.Client(
            config=enapter.http.api.Config(
                token=token, base_url=self._enaper_http_api_url
            )
        )
