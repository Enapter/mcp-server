import asyncio
import datetime
import re

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .command_execution_search_query import CommandExecutionSearchQuery
from .device_dto import DeviceDTO
from .device_search_query import DeviceSearchQuery
from .enapter_api import EnapterAPI
from .errors import SearchQueryTooBroad
from .rule_search_query import RuleSearchQuery
from .site_dto import SiteDTO
from .site_search_query import SiteSearchQuery


class ApplicationServer:

    def __init__(self, enapter_api: EnapterAPI) -> None:
        self._enapter_api = enapter_api

    async def search_sites(
        self,
        auth: AuthConfig,
        query: SiteSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.Site]:
        sites = await self._search_sites(auth, query)
        sites.sort(key=lambda s: s.id)
        return sites[offset : offset + limit]

    async def _search_sites(
        self, auth: AuthConfig, query: SiteSearchQuery
    ) -> list[domain.Site]:
        semaphore = asyncio.Semaphore(10)

        async def fetch(site_dto: SiteDTO) -> domain.Site:
            async with semaphore:
                return await self._fetch_site_context(auth, site_dto)

        tasks = []
        async with asyncio.TaskGroup() as tg:
            async with self._enapter_api.list_sites(auth) as sites_gen:
                async for site_dto in sites_gen:
                    if not query.matches(site_dto):
                        continue

                    task = tg.create_task(fetch(site_dto))
                    tasks.append(task)

        return [task.result() for task in tasks]

    async def _fetch_site_context(
        self, auth: AuthConfig, site_dto: SiteDTO
    ) -> domain.Site:
        gateway_id: str | None = None
        gateway_online = False
        devices_online = 0
        device_ids: list[str] = []

        async with self._enapter_api.list_devices(
            auth, site_id=site_dto.id, expand_connectivity=True
        ) as devices_gen:
            async for device_dto in devices_gen:
                device_ids.append(device_dto.id)
                is_online = device_dto.connectivity == domain.ConnectivityStatus.ONLINE
                if is_online:
                    devices_online += 1

                if device_dto.type == domain.DeviceType.GATEWAY:
                    gateway_id = device_dto.id
                    gateway_online = is_online

        rule_engine_state: domain.RuleEngineState | None = None
        if gateway_online:
            engine_dto = await self._enapter_api.get_rule_engine(auth, site_dto.id)
            rule_engine_state = engine_dto.state

        return domain.Site(
            id=site_dto.id,
            name=site_dto.name,
            timezone=site_dto.timezone,
            gateway_id=gateway_id,
            gateway_online=gateway_online,
            devices_total=len(device_ids),
            devices_online=devices_online,
            rule_engine_state=rule_engine_state,
        )

    async def search_rules(
        self,
        auth: AuthConfig,
        query: RuleSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.Rule]:
        rules = await self._search_rules(auth, query)
        rules.sort(key=lambda r: r.id)
        return rules[offset : offset + limit]

    async def _search_rules(
        self, auth: AuthConfig, query: RuleSearchQuery
    ) -> list[domain.Rule]:
        rules: list[domain.Rule] = []
        async with self._enapter_api.list_rules(auth, query.site_id) as rules_gen:
            async for rule_dto in rules_gen:
                if not query.matches(rule_dto):
                    continue

                rules.append(
                    domain.Rule(
                        id=rule_dto.id,
                        slug=rule_dto.slug,
                        enabled=not rule_dto.disabled,
                        state=rule_dto.state,
                        script_summary=domain.RuleScriptSummary(
                            runtime_version=rule_dto.script_runtime_version,
                            exec_interval=rule_dto.script_exec_interval,
                            lines_count=len(rule_dto.script_code.splitlines()),
                        ),
                    )
                )

        return rules

    async def read_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        rule_id: str,
        offset: int,
        limit: int,
    ) -> list[str]:
        rule_dto = await self._enapter_api.get_rule(auth, site_id, rule_id)
        lines = rule_dto.script_code.splitlines()
        return lines[offset : offset + limit]

    async def search_devices(
        self,
        auth: AuthConfig,
        query: DeviceSearchQuery,
        offset: int,
        limit: int,
        view: domain.DeviceView,
    ) -> list[domain.Device]:
        match view:
            case domain.DeviceView.BASIC:
                devices = await self._search_devices_basic(auth, query)
            case domain.DeviceView.FULL:
                devices = await self._search_devices_full(auth, query)
            case _:
                raise NotImplementedError(view)

        devices.sort(key=lambda d: d.id)
        return devices[offset : offset + limit]

    async def _search_devices_basic(
        self, auth: AuthConfig, query: DeviceSearchQuery
    ) -> list[domain.Device]:
        devices: list[domain.Device] = []
        async with self._enapter_api.list_devices(
            auth,
            site_id=query.site_id,
            expand_manifest=True,
            expand_connectivity=True,
            expand_active_alerts=True,
        ) as devices_gen:
            async for device_dto in devices_gen:
                if query.matches(device_dto):
                    assert device_dto.manifest is not None
                    assert device_dto.connectivity is not None
                    assert device_dto.active_alerts is not None
                    devices.append(
                        domain.Device(
                            id=device_dto.id,
                            name=device_dto.name,
                            site_id=device_dto.site_id,
                            type=device_dto.type,
                            blueprint_summary=domain.BlueprintSummary.from_device_manifest(
                                device_dto.manifest
                            ),
                            connectivity_status=device_dto.connectivity,
                            active_alerts_total=len(device_dto.active_alerts),
                        )
                    )

        return devices

    async def _search_devices_full(
        self, auth: AuthConfig, query: DeviceSearchQuery
    ) -> list[domain.Device]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `site_id` or `device_id` to narrow down the search."
            )

        matched_device_dtos: list[DeviceDTO] = []
        async with self._enapter_api.list_devices(
            auth,
            site_id=query.site_id,
            expand_manifest=True,
            expand_properties=True,
            expand_connectivity=True,
            expand_active_alerts=True,
        ) as devices_gen:
            async for device_dto in devices_gen:
                if query.matches(device_dto):
                    matched_device_dtos.append(device_dto)

        if not matched_device_dtos:
            return []

        devices: list[domain.Device] = []
        for device_dto in matched_device_dtos:
            assert device_dto.manifest is not None
            assert device_dto.connectivity is not None
            assert device_dto.properties is not None
            assert device_dto.active_alerts is not None
            devices.append(
                domain.Device(
                    id=device_dto.id,
                    name=device_dto.name,
                    site_id=device_dto.site_id,
                    type=device_dto.type,
                    blueprint_summary=domain.BlueprintSummary.from_device_manifest(
                        device_dto.manifest
                    ),
                    connectivity_status=device_dto.connectivity,
                    active_alerts_total=len(device_dto.active_alerts),
                    properties={
                        k: device_dto.properties.get(k)
                        for k in device_dto.manifest.properties
                    },
                    active_alerts=device_dto.active_alerts,
                )
            )

        return devices

    async def read_blueprint(
        self,
        auth: AuthConfig,
        device_id: str,
        section: domain.BlueprintSection,
        name_regexp: str,
        offset: int,
        limit: int,
    ) -> list[
        domain.PropertyDeclaration
        | domain.TelemetryAttributeDeclaration
        | domain.AlertDeclaration
        | domain.CommandDeclaration
    ]:
        name_pattern = re.compile(name_regexp)
        device_dto = await self._enapter_api.get_device(
            auth, device_id, expand_manifest=True
        )
        assert device_dto.manifest is not None

        entities: list[
            domain.PropertyDeclaration
            | domain.TelemetryAttributeDeclaration
            | domain.AlertDeclaration
            | domain.CommandDeclaration
        ]

        match section:
            case domain.BlueprintSection.PROPERTIES:
                entities = list(device_dto.manifest.properties.values())
            case domain.BlueprintSection.TELEMETRY:
                entities = list(device_dto.manifest.telemetry.values())
            case domain.BlueprintSection.ALERTS:
                entities = list(device_dto.manifest.alerts.values())
            case domain.BlueprintSection.COMMANDS:
                entities = list(device_dto.manifest.commands.values())
            case _:
                raise NotImplementedError(section)

        entities = [e for e in entities if name_pattern.search(e.name)]
        entities.sort(key=lambda e: e.name)
        return entities[offset : offset + limit]

    async def get_historical_telemetry(
        self,
        auth: AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry:
        return await self._enapter_api.get_historical_telemetry(
            auth,
            device_id,
            attributes,
            time_from,
            time_to,
            granularity,
            aggregation,
        )

    async def search_command_executions(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
        view: domain.CommandExecutionView,
    ) -> list[domain.CommandExecution]:
        match view:
            case domain.CommandExecutionView.BASIC:
                return await self._search_command_executions_basic(
                    auth, query, offset, limit
                )
            case domain.CommandExecutionView.FULL:
                return await self._search_command_executions_full(
                    auth, query, offset, limit
                )
            case _:
                raise NotImplementedError(view)

    async def _search_command_executions_basic(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.CommandExecution]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `site_id` or `device_id` to narrow down the search."
            )

        executions: list[domain.CommandExecution] = []
        skipped = 0

        async with self._enapter_api.list_command_executions(
            auth,
            device_id=query.device_id,
            site_id=query.site_id,
            created_at_gte=query.created_at_gte,
            created_at_lt=query.created_at_lt,
            state=query.state,
        ) as executions_gen:
            async for execution in executions_gen:
                if query.matches(execution):
                    if skipped < offset:
                        skipped += 1
                        continue

                    executions.append(execution.strip())
                    if len(executions) >= limit:
                        break

        return executions

    async def _search_command_executions_full(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.CommandExecution]:
        if query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `device_id` to narrow down the search."
            )

        executions: list[domain.CommandExecution] = []
        skipped = 0

        async with self._enapter_api.list_command_executions(
            auth,
            device_id=query.device_id,
            site_id=query.site_id,
            created_at_gte=query.created_at_gte,
            created_at_lt=query.created_at_lt,
            state=query.state,
        ) as executions_gen:
            async for execution in executions_gen:
                if query.matches(execution):
                    if skipped < offset:
                        skipped += 1
                        continue

                    executions.append(execution)
                    if len(executions) >= limit:
                        break

        return executions
