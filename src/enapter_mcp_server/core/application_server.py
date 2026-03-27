import dataclasses
import datetime
import re

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .enapter_api import EnapterAPI


class ApplicationServer:

    def __init__(self, enapter_api: EnapterAPI) -> None:
        self._enapter_api = enapter_api

    async def search_sites(
        self,
        auth: AuthConfig,
        spec: domain.SiteSpecification,
        offset: int,
        limit: int,
    ) -> list[domain.Site]:
        sites = []
        async with self._enapter_api.list_sites(auth) as sites_gen:
            async for site in sites_gen:
                if spec.matches(site):
                    sites.append(site)

        sites.sort(key=lambda s: s.id)
        return sites[offset : offset + limit]

    async def get_site_details(
        self, auth: AuthConfig, site_id: str
    ) -> domain.SiteDetails:
        site = await self._enapter_api.get_site(auth, site_id)

        gateway_id: str | None = None
        gateway_online = False
        devices_total = 0
        devices_online = 0
        active_alerts_total = 0
        device_ids: list[str] = []

        async with self._enapter_api.list_devices(
            auth, site_id=site_id, expand_connectivity=True
        ) as devices_gen:
            async for device_dto in devices_gen:
                device_ids.append(device_dto.id)
                is_online = device_dto.connectivity == domain.ConnectivityStatus.ONLINE
                if is_online:
                    devices_online += 1

                if device_dto.type == domain.DeviceType.GATEWAY:
                    gateway_id = device_dto.id
                    gateway_online = is_online

        latest_telemetry_by_device = await self._enapter_api.get_latest_telemetry(
            auth, {device_id: ["alerts"] for device_id in device_ids}
        )
        active_alerts_total = sum(
            len(device_telemetry.get("alerts") or [])
            for device_telemetry in latest_telemetry_by_device.values()
        )
        devices_total = len(device_ids)

        return domain.SiteDetails(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            site=site,
            gateway_id=gateway_id,
            gateway_online=gateway_online,
            devices_total=devices_total,
            devices_online=devices_online,
            active_alerts_total=active_alerts_total,
        )

    async def search_devices(
        self,
        auth: AuthConfig,
        spec: domain.DeviceSpecification,
        offset: int,
        limit: int,
    ) -> list[domain.Device]:
        devices = []
        async with self._enapter_api.list_devices(
            auth, site_id=spec.site_id
        ) as devices_gen:
            async for device_dto in devices_gen:
                device = device_dto.to_domain()
                if spec.matches(device):
                    devices.append(device)

        devices.sort(key=lambda d: d.id)
        return devices[offset : offset + limit]

    async def get_device_details(
        self, auth: AuthConfig, device_id: str
    ) -> domain.Device:
        device_dto = await self._enapter_api.get_device(
            auth,
            device_id,
            expand_manifest=True,
            expand_connectivity=True,
            expand_properties=True,
        )
        assert device_dto.manifest is not None
        assert device_dto.connectivity is not None
        assert device_dto.properties is not None
        latest_telemetry = await self._enapter_api.get_latest_telemetry(
            auth, {device_id: ["alerts"]}
        )

        blueprint_summary = domain.BlueprintSummary(
            description=device_dto.manifest.get("description"),
            vendor=device_dto.manifest.get("vendor"),
            commands_total=len(device_dto.manifest.get("commands") or {}),
            properties_total=len(device_dto.manifest.get("properties") or {}),
            telemetry_attributes_total=len(device_dto.manifest.get("telemetry") or {}),
            alerts_total=len(device_dto.manifest.get("alerts") or {}),
        )

        device = device_dto.to_domain()

        return dataclasses.replace(
            device,
            connectivity_status=device_dto.connectivity,
            properties={
                k: device_dto.properties.get(k)
                for k in device_dto.manifest.get("properties", {})
            },
            active_alerts=latest_telemetry.get(device_id, {}).get("alerts") or [],
            blueprint_summary=blueprint_summary,
        )

    async def read_blueprint_manifest(
        self,
        auth: AuthConfig,
        device_id: str,
        section: domain.BlueprintManifestSection,
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
            case domain.BlueprintManifestSection.PROPERTIES:
                entities = [
                    domain.PropertyDeclaration(
                        name=name,
                        display_name=dto["display_name"],
                        data_type=domain.DataType(dto["type"]),
                        description=dto.get("description"),
                        enum=dto.get("enum"),
                        unit=dto.get("unit"),
                    )
                    for name, dto in (
                        device_dto.manifest.get("properties") or {}
                    ).items()
                ]
            case domain.BlueprintManifestSection.TELEMETRY:
                entities = [
                    domain.TelemetryAttributeDeclaration(
                        name=name,
                        display_name=dto["display_name"],
                        data_type=domain.DataType(dto["type"]),
                        description=dto.get("description"),
                        enum=dto.get("enum"),
                        unit=dto.get("unit"),
                    )
                    for name, dto in (
                        device_dto.manifest.get("telemetry") or {}
                    ).items()
                ]
            case domain.BlueprintManifestSection.ALERTS:
                entities = [
                    domain.AlertDeclaration(
                        name=name,
                        display_name=dto["display_name"],
                        severity=domain.AlertSeverity(dto["severity"]),
                        description=dto.get("description"),
                        troubleshooting=dto.get("troubleshooting"),
                        components=dto.get("components"),
                        conditions=dto.get("conditions"),
                    )
                    for name, dto in (device_dto.manifest.get("alerts") or {}).items()
                ]
            case domain.BlueprintManifestSection.COMMANDS:
                entities = [
                    domain.CommandDeclaration(
                        name=name,
                        display_name=dto.get("display_name", name),
                        description=dto.get("description"),
                        arguments=[
                            domain.CommandArgumentDeclaration(
                                name=arg_name,
                                display_name=arg_dto.get("display_name", arg_name),
                                data_type=domain.DataType(arg_dto["type"]),
                                required=arg_dto.get("required", False),
                                description=arg_dto.get("description"),
                                enum=arg_dto.get("enum"),
                            )
                            for arg_name, arg_dto in (
                                dto.get("arguments") or {}
                            ).items()
                        ],
                    )
                    for name, dto in (device_dto.manifest.get("commands") or {}).items()
                ]
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
