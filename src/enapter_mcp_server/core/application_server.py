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

        async with self._enapter_api.list_devices(
            auth, site_id=site_id, expand_connectivity=True
        ) as devices_gen:
            async for device_dto in devices_gen:
                devices_total += 1
                is_online = device_dto.connectivity == domain.ConnectivityStatus.ONLINE
                if is_online:
                    devices_online += 1

                if device_dto.type == domain.DeviceType.GATEWAY:
                    gateway_id = device_dto.id
                    gateway_online = is_online

        return domain.SiteDetails(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            site=site,
            gateway_id=gateway_id,
            gateway_online=gateway_online,
            devices_total=devices_total,
            devices_online=devices_online,
        )

    async def search_devices(
        self,
        auth: AuthConfig,
        spec: domain.DeviceSpecification,
        offset: int,
        limit: int,
    ) -> list[domain.Device]:
        devices = []
        async with self._enapter_api.list_devices(auth, site_id=spec.site_id) as devices_gen:
            async for device_dto in devices_gen:
                device = device_dto.to_domain()
                if spec.matches(device):
                    devices.append(device)

        devices.sort(key=lambda d: d.id)
        return devices[offset : offset + limit]

    async def get_device_details(
        self, auth: AuthConfig, device_id: str
    ) -> domain.DeviceDetails:
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
            auth, device_id, list(device_dto.manifest.get("telemetry", {}))
        )

        blueprint_summary = domain.BlueprintSummary(
            description=device_dto.manifest.get("description"),
            vendor=device_dto.manifest.get("vendor"),
            properties_total=len(device_dto.manifest.get("properties", {})),
            telemetry_attributes_total=len(device_dto.manifest.get("telemetry", {})),
            alerts_total=len(device_dto.manifest.get("alerts", {})),
        )

        device = device_dto.to_domain()

        return domain.DeviceDetails(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            device=device,
            connectivity_status=device_dto.connectivity,
            properties={
                k: device_dto.properties.get(k)
                for k in device_dto.manifest.get("properties", {})
            },
            latest_telemetry=latest_telemetry,
            blueprint_summary=blueprint_summary,
        )

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
        ]

        match section:
            case domain.BlueprintSection.PROPERTIES:
                entities = [
                    domain.PropertyDeclaration(
                        name=name,
                        display_name=dto["display_name"],
                        data_type=domain.PropertyDataType(dto["type"]),
                        description=dto.get("description"),
                        enum=dto.get("enum"),
                        unit=dto.get("unit"),
                    )
                    for name, dto in device_dto.manifest.get("properties", {}).items()
                ]
            case domain.BlueprintSection.TELEMETRY:
                entities = [
                    domain.TelemetryAttributeDeclaration(
                        name=name,
                        display_name=dto["display_name"],
                        data_type=domain.TelemetryAttributeDataType(dto["type"]),
                        description=dto.get("description"),
                        enum=dto.get("enum"),
                        unit=dto.get("unit"),
                    )
                    for name, dto in device_dto.manifest.get("telemetry", {}).items()
                ]
            case domain.BlueprintSection.ALERTS:
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
                    for name, dto in device_dto.manifest.get("alerts", {}).items()
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
