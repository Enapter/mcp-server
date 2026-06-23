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
                    yield self._data_mapper.to_site_dto(site)

    async def get_rule_engine(
        self, auth: core.AuthConfig, site_id: str
    ) -> core.RuleEngineDTO:
        async with self._new_client(auth) as client:
            engine = await client.rule_engine.get(site_id)
            return core.RuleEngineDTO(
                id=engine.id,
                state=domain.RuleEngineState(engine.state.value.lower()),
                timezone=engine.timezone,
            )

    @enapter.async_.generator
    async def list_rules(
        self, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[core.RuleDTO, None]:
        async with self._new_client(auth) as client:
            async with client.rule_engine.list_rules(site_id) as rules:
                async for rule in rules:
                    yield core.RuleDTO(
                        id=rule.id,
                        slug=rule.slug,
                        disabled=rule.disabled,
                        state=domain.RuleState(rule.state.value.lower()),
                        script_runtime_version=domain.RuleRuntimeVersion(
                            rule.script.runtime_version.value.lower()
                        ),
                        script_exec_interval=rule.script.exec_interval,
                        script_code=rule.script.code,
                    )

    async def get_rule(
        self, auth: core.AuthConfig, site_id: str, rule_id: str
    ) -> core.RuleDTO:
        async with self._new_client(auth) as client:
            rule = await client.rule_engine.get_rule(rule_id, site_id)
            return core.RuleDTO(
                id=rule.id,
                slug=rule.slug,
                disabled=rule.disabled,
                state=domain.RuleState(rule.state.value.lower()),
                script_runtime_version=domain.RuleRuntimeVersion(
                    rule.script.runtime_version.value.lower()
                ),
                script_exec_interval=rule.script.exec_interval,
                script_code=rule.script.code,
            )

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
        expand_active_alerts: bool = False,
    ) -> AsyncGenerator[core.DeviceDTO, None]:
        async with self._new_client(auth) as client:
            async with client.devices.list(
                site_id=site_id,
                expand_manifest=expand_manifest,
                expand_properties=expand_properties,
                expand_connectivity=expand_connectivity,
                expand_raised_alert_names=expand_active_alerts,
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
        expand_active_alerts: bool = False,
    ) -> core.DeviceDTO:
        async with self._new_client(auth) as client:
            device = await client.devices.get(
                device_id,
                expand_manifest=expand_manifest,
                expand_connectivity=expand_connectivity,
                expand_properties=expand_properties,
                expand_raised_alert_names=expand_active_alerts,
            )
            return self._data_mapper.to_device_dto(device)

    async def execute_command(
        self,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution:
        async with self._new_client(auth) as client:
            execution = await client.commands.execute(
                device_id, command_name, arguments
            )
            return self._data_mapper.to_command_execution(execution)

    @enapter.async_.generator
    async def list_command_executions(
        self,
        auth: core.AuthConfig,
        device_id: str | None = None,
        site_id: str | None = None,
        created_at_gte: datetime.datetime | None = None,
        created_at_lt: datetime.datetime | None = None,
        state: domain.CommandExecutionState | None = None,
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        async with self._new_client(auth) as client:
            async with client.commands.list_executions(
                device_id=device_id,
                site_id=site_id,
                created_at_gte=created_at_gte,
                created_at_lt=created_at_lt,
                state=(
                    self._data_mapper.from_command_execution_state(state)
                    if state
                    else None
                ),
                order=enapter.http.api.commands.ListExecutionsOrder.CREATED_AT_DESC,
            ) as executions:
                async for execution in executions:
                    yield self._data_mapper.to_command_execution(execution)

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
        aggregation: domain.AggregationFunction,
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
                        aggregation=enapter.http.api.telemetry.Aggregation(
                            aggregation.value.upper()
                        ),
                    )
                ],
            )
            return self._data_mapper.to_historical_telemetry(telemetry)

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
