import contextlib
import datetime
from typing import Any, AsyncGenerator, Self

import enapter

from enapter_mcp_server import core, domain

from .enapter_data_mapper import EnapterDataMapper


class EnapterAPI:

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._transport = enapter.http.api.Transport()
        self._data_mapper = EnapterDataMapper()

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
                    yield self._data_mapper.to_device_dto(device)

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
            return self._data_mapper.to_device_dto(device)

    @enapter.async_.generator
    async def list_command_executions(
        self, auth: core.AuthConfig, device_id: str
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        async with self._new_client(auth) as client:
            async with client.commands.list_executions(device_id) as executions:
                async for execution in executions:
                    yield self._data_mapper.to_command_execution(device_id, execution)

    async def get_latest_telemetry(
        self, auth: core.AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]:
        async with self._new_client(auth) as client:
            try:
                return self._data_mapper.to_latest_telemetry(
                    await client.telemetry.latest(attributes_by_device)
                )
            except (enapter.http.api.Error, enapter.http.api.MultiError) as exc:
                raise core.LatestTelemetryUnavailable() from exc

    async def get_historical_telemetry(
        self,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: enapter.http.api.telemetry.Aggregation,
    ) -> domain.HistoricalTelemetry:
        async with self._new_client(auth) as client:
            telemetry = await client.telemetry.wide_timeseries(
                from_=time_from,
                to=time_to,
                granularity=granularity,
                selectors=[
                    enapter.http.api.telemetry.Selector(
                        device=device_id,
                        attributes=attributes,
                        aggregation=aggregation,
                    )
                ],
            )
            return self._data_mapper.to_historical_telemetry(telemetry)

    async def get_historical_telemetry_stats(
        self,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
    ) -> domain.HistoricalTelemetryStats:
        granularity = int((time_to - time_from).total_seconds())
        aggregations = [
            enapter.http.api.telemetry.Aggregation.MIN,
            enapter.http.api.telemetry.Aggregation.MAX,
            enapter.http.api.telemetry.Aggregation.AVG,
            enapter.http.api.telemetry.Aggregation.LAST,
        ]
        async with self._new_client(auth) as client:
            telemetry = await client.telemetry.wide_timeseries(
                from_=time_from,
                to=time_to,
                granularity=granularity,
                selectors=[
                    enapter.http.api.telemetry.Selector(
                        device=device_id, attributes=attributes, aggregation=a
                    )
                    for a in aggregations
                ],
            )

        buckets: dict[str, dict[str, list[Any]]] = {
            a.value.lower(): {} for a in aggregations
        }
        for column in telemetry.columns:
            buckets[column.labels["aggregation"]][column.labels.telemetry] = (
                column.values
            )

        # Platform API may return 1-2 points per attribute when PG time_bucket
        # boundaries don't align with time_from; reduce to one scalar.
        def reduce(
            by_attr: dict[str, list[Any]], reducer: Any
        ) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for attr, values in by_attr.items():
                non_null = [v for v in values if v is not None]
                out[attr] = reducer(non_null) if non_null else None
            return out

        min_by_attr = reduce(buckets["min"], min)
        max_by_attr = reduce(buckets["max"], max)
        avg_by_attr = reduce(buckets["avg"], lambda xs: sum(xs) / len(xs))
        last_by_attr = reduce(buckets["last"], lambda xs: xs[-1])

        return domain.HistoricalTelemetryStats(
            values={
                attr: domain.HistoricalTelemetryAttributeStats(
                    min=min_by_attr.get(attr),
                    max=max_by_attr.get(attr),
                    avg=avg_by_attr.get(attr),
                    last=last_by_attr.get(attr),
                )
                for attr in attributes
            }
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
