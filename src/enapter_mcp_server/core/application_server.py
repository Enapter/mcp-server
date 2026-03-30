import datetime
import re

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .command_execution_search_query import CommandExecutionSearchQuery
from .device_dto import DeviceDTO
from .device_search_query import DeviceSearchQuery
from .enapter_api import EnapterAPI
from .errors import (
    LatestTelemetryUnavailable,
    SearchQueryTooBroad,
)
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
        sites: list[domain.Site] = []
        async with self._enapter_api.list_sites(auth) as sites_gen:
            async for site_dto in sites_gen:
                if not query.matches(site_dto):
                    continue
                gateway_id: str | None = None
                gateway_online = False
                devices_online = 0
                device_ids: list[str] = []

                async with self._enapter_api.list_devices(
                    auth, site_id=site_dto.id, expand_connectivity=True
                ) as devices_gen:
                    async for device_dto in devices_gen:
                        device_ids.append(device_dto.id)
                        is_online = (
                            device_dto.connectivity == domain.ConnectivityStatus.ONLINE
                        )
                        if is_online:
                            devices_online += 1

                        if device_dto.type == domain.DeviceType.GATEWAY:
                            gateway_id = device_dto.id
                            gateway_online = is_online

                sites.append(
                    domain.Site(
                        id=site_dto.id,
                        name=site_dto.name,
                        timezone=site_dto.timezone,
                        gateway_id=gateway_id,
                        gateway_online=gateway_online,
                        devices_total=len(device_ids),
                        devices_online=devices_online,
                    )
                )

        return sites

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
        ) as devices_gen:
            async for device_dto in devices_gen:
                if query.matches(device_dto):
                    assert device_dto.manifest is not None
                    assert device_dto.connectivity is not None
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
                        )
                    )

        return devices

    async def _search_devices_full(
        self, auth: AuthConfig, query: DeviceSearchQuery
    ) -> list[domain.Device]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "FULL device search requires site_id or device_id"
            )

        matched_device_dtos: list[DeviceDTO] = []
        async with self._enapter_api.list_devices(
            auth,
            site_id=query.site_id,
            expand_manifest=True,
            expand_properties=True,
            expand_connectivity=True,
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
                    properties={
                        k: device_dto.properties.get(k)
                        for k in device_dto.manifest.properties
                    },
                    active_alerts=await self._get_active_alerts(auth, device_dto.id),
                )
            )

        return devices

    async def _get_active_alerts(self, auth: AuthConfig, device_id: str) -> list[str]:
        try:
            latest_telemetry = await self._enapter_api.get_latest_telemetry(
                auth, {device_id: ["alerts"]}
            )
        except LatestTelemetryUnavailable:
            return []
        return latest_telemetry.get(device_id, {}).get("alerts") or []

    async def read_blueprint(
        self,
        auth: AuthConfig,
        device_id: str,
        section: domain.BlueprintSection,
        name_pattern: str,
        offset: int,
        limit: int,
    ) -> list[
        domain.PropertyDeclaration
        | domain.TelemetryAttributeDeclaration
        | domain.AlertDeclaration
        | domain.CommandDeclaration
    ]:
        name_regexp = re.compile(name_pattern)
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

        entities = [e for e in entities if name_regexp.search(e.name)]
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
    ) -> domain.HistoricalTelemetry:
        return await self._enapter_api.get_historical_telemetry(
            auth, device_id, attributes, time_from, time_to, granularity
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
                executions = await self._search_command_executions_basic(auth, query)
            case domain.CommandExecutionView.FULL:
                executions = await self._search_command_executions_full(auth, query)
            case _:
                raise NotImplementedError(view)

        executions.sort(key=lambda e: e.created_at, reverse=True)
        return executions[offset : offset + limit]

    async def _search_command_executions_basic(
        self, auth: AuthConfig, query: CommandExecutionSearchQuery
    ) -> list[domain.CommandExecution]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "Command execution search requires site_id or device_id"
            )

        device_ids: list[str] = []
        async with self._enapter_api.list_devices(
            auth, site_id=query.site_id
        ) as devices_gen:
            async for device_dto in devices_gen:
                if query.device_id is None or device_dto.id == query.device_id:
                    device_ids.append(device_dto.id)

        executions: list[domain.CommandExecution] = []
        for device_id in device_ids:
            async with self._enapter_api.list_command_executions(
                auth, device_id=device_id
            ) as executions_gen:
                async for execution in executions_gen:
                    if query.matches(execution):
                        executions.append(execution.strip())

        return executions

    async def _search_command_executions_full(
        self, auth: AuthConfig, query: CommandExecutionSearchQuery
    ) -> list[domain.CommandExecution]:
        if query.device_id is None:
            raise SearchQueryTooBroad(
                "FULL command execution search requires device_id"
            )

        if query.site_id is not None:
            device_dto = await self._enapter_api.get_device(auth, query.device_id)
            if device_dto.site_id != query.site_id:
                return []

        executions: list[domain.CommandExecution] = []
        async with self._enapter_api.list_command_executions(
            auth, device_id=query.device_id
        ) as executions_gen:
            async for execution in executions_gen:
                if query.matches(execution):
                    executions.append(execution)

        return executions
