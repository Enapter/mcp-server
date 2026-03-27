import contextlib
import datetime
from typing import Any, AsyncGenerator, Self

import enapter

from enapter_mcp_server import core, domain


class EnapterAPI:

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._transport = enapter.http.api.Transport()

    async def __aenter__(self) -> Self:
        await self._transport.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._transport.__aexit__(*args)

    @enapter.async_.generator
    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[core.SiteDTO, None]:
        async with self._new_client(auth) as client:
            async with client.sites.list() as s:
                async for site in s:
                    yield core.SiteDTO(
                        id=site.id,
                        name=site.name,
                        timezone=site.timezone,
                    )

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
    ) -> AsyncGenerator[core.DeviceDTO, None]:
        async with self._new_client(auth) as client:
            async with client.devices.list(
                site_id=site_id,
                expand_manifest=expand_manifest,
                expand_properties=expand_properties,
                expand_connectivity=expand_connectivity,
            ) as s:
                async for device in s:
                    connectivity = None
                    if device.connectivity is not None:
                        connectivity = domain.ConnectivityStatus(
                            device.connectivity.status.value
                        )

                    yield core.DeviceDTO(
                        id=device.id,
                        name=device.name,
                        site_id=device.site_id,
                        type=domain.DeviceType(device.type.value),
                        connectivity=connectivity,
                        properties=device.properties,
                        manifest=device.manifest,
                    )

    async def get_device(
        self,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
    ) -> core.DeviceDTO:
        async with self._new_client(auth) as client:
            device = await client.devices.get(
                device_id,
                expand_manifest=expand_manifest,
                expand_connectivity=expand_connectivity,
                expand_properties=expand_properties,
            )

            connectivity = None
            if device.connectivity is not None:
                connectivity = domain.ConnectivityStatus(
                    device.connectivity.status.value
                )

            return core.DeviceDTO(
                id=device.id,
                name=device.name,
                site_id=device.site_id,
                type=domain.DeviceType(device.type.value),
                connectivity=connectivity,
                properties=device.properties,
                manifest=device.manifest,
            )

    async def get_latest_telemetry(
        self, auth: core.AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]:
        async with self._new_client(auth) as client:
            return {
                device_id: {
                    k: v.value if v is not None else None
                    for k, v in device_telemetry.items()
                }
                for device_id, device_telemetry in (
                    await client.telemetry.latest(attributes_by_device)
                ).items()
            }

    async def get_historical_telemetry(
        self,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
    ) -> domain.HistoricalTelemetry:
        async with self._new_client(auth) as client:
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
            return domain.HistoricalTelemetry(
                timestamps=telemetry.timestamps,
                values={
                    column.labels.telemetry: column.values
                    for column in telemetry.columns
                },
            )

    @contextlib.asynccontextmanager
    async def _new_client(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[enapter.http.api.Client, None]:
        config = enapter.http.api.Config(
            base_url=self._base_url, token=auth.token, user=auth.user
        )
        async with enapter.http.api.Client(
            config=config, transport=self._transport
        ) as client:
            yield client
