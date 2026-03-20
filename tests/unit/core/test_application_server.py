import datetime
from typing import Any, AsyncGenerator

from enapter_mcp_server import core, domain


class MockEnapterAPI:
    def __init__(
        self,
        sites: list[domain.Site] | None = None,
        devices: list[core.DeviceDTO] | None = None,
        telemetry: dict[str, Any] | None = None,
        historical_telemetry: domain.HistoricalTelemetry | None = None,
    ):
        self._sites = sites or []
        self._devices = devices or []
        self._telemetry = telemetry or {}
        self._historical_telemetry = historical_telemetry

    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
        for site in self._sites:
            yield site

    async def get_site(self, auth: core.AuthConfig, site_id: str) -> domain.Site:
        for site in self._sites:
            if site.id == site_id:
                return site
        raise ValueError(f"Site {site_id} not found")

    async def list_devices(
        self,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_connectivity: bool = False,
    ) -> AsyncGenerator[core.DeviceDTO, None]:
        for device in self._devices:
            if site_id is None or device.site_id == site_id:
                yield device

    async def get_device(
        self,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
    ) -> core.DeviceDTO:
        for device in self._devices:
            if device.id == device_id:
                return device
        raise ValueError(f"Device {device_id} not found")

    async def get_latest_telemetry(
        self, auth: core.AuthConfig, device_id: str, attributes: list[str]
    ) -> dict[str, Any]:
        return self._telemetry.get(device_id, {})

    async def get_historical_telemetry(
        self,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
    ) -> domain.HistoricalTelemetry:
        if self._historical_telemetry is None:
            raise NotImplementedError()
        return self._historical_telemetry


class TestApplicationServer:

    async def test_search_sites_filtering(self) -> None:
        sites = [
            domain.Site(id="1", name="Alpha", timezone="Europe/Berlin"),
            domain.Site(id="2", name="Beta", timezone="Europe/London"),
            domain.Site(id="3", name="Gamma", timezone="Europe/Berlin"),
        ]
        api = MockEnapterAPI(sites=sites)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Test name filtering
        result = await app.search_sites(
            auth, name_pattern="Alpha", timezone_pattern=".*", offset=0, limit=20
        )
        assert len(result) == 1
        assert result[0].name == "Alpha"

        # Test timezone filtering
        result = await app.search_sites(
            auth, name_pattern=".*", timezone_pattern="Berlin", offset=0, limit=20
        )
        assert len(result) == 2
        assert result[0].name == "Alpha"
        assert result[1].name == "Gamma"

        # Test sorting and pagination
        result = await app.search_sites(
            auth, name_pattern=".*", timezone_pattern=".*", offset=0, limit=1
        )
        assert len(result) == 1
        assert result[0].id == "1"

    async def test_get_site_context(self) -> None:
        site = domain.Site(id="site-1", name="Site 1", timezone="UTC")
        devices = [
            core.DeviceDTO(
                id="dev-1",
                name="Gateway",
                site_id="site-1",
                type=domain.DeviceType.GATEWAY,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            core.DeviceDTO(
                id="dev-2",
                name="Device 2",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
        ]
        api = MockEnapterAPI(sites=[site], devices=devices)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        context = await app.get_site_context(auth, "site-1")

        assert context.site.id == "site-1"
        assert context.gateway_id == "dev-1"
        assert context.gateway_online is True
        assert context.devices_total == 2
        assert context.devices_online == 1

    async def test_search_devices(self) -> None:
        devices = [
            core.DeviceDTO(
                id="1", name="Alpha", site_id="s1", type=domain.DeviceType.NATIVE
            ),
            core.DeviceDTO(
                id="2", name="Beta", site_id="s1", type=domain.DeviceType.GATEWAY
            ),
            core.DeviceDTO(
                id="3", name="Gamma", site_id="s2", type=domain.DeviceType.NATIVE
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Filter by site
        result = await app.search_devices(
            auth, site_id="s1", device_type=None, name_pattern=".*", offset=0, limit=10
        )
        assert len(result) == 2

        # Filter by type
        result = await app.search_devices(
            auth,
            site_id=None,
            device_type=domain.DeviceType.GATEWAY,
            name_pattern=".*",
            offset=0,
            limit=10,
        )
        assert len(result) == 1
        assert result[0].id == "2"

    async def test_get_device_context(self) -> None:
        manifest = {
            "description": "Desc",
            "vendor": "Enapter",
            "properties": {"p1": {}},
            "telemetry": {"t1": {}},
            "alerts": {"a1": {}},
        }
        device = core.DeviceDTO(
            id="dev-1",
            name="Dev 1",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            connectivity=domain.ConnectivityStatus.ONLINE,
            properties={"p1": "v1"},
            manifest=manifest,
        )
        telemetry = {"dev-1": {"t1": 42}}
        api = MockEnapterAPI(devices=[device], telemetry=telemetry)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        context = await app.get_device_context(auth, "dev-1")

        assert context.device.id == "dev-1"
        assert context.connectivity_status == domain.ConnectivityStatus.ONLINE
        assert context.properties == {"p1": "v1"}
        assert context.latest_telemetry == {"t1": 42}
        assert context.blueprint_summary.properties_total == 1

    async def test_read_blueprint(self) -> None:
        manifest = {
            "properties": {
                "p1": {"display_name": "P1", "type": "string", "description": "D1"}
            },
            "telemetry": {"t1": {"display_name": "T1", "type": "float", "unit": "V"}},
            "alerts": {"a1": {"display_name": "A1", "severity": "warning"}},
        }
        device = core.DeviceDTO(
            id="dev-1",
            name="Dev 1",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            manifest=manifest,
        )
        api = MockEnapterAPI(devices=[device])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Read properties
        props = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.PROPERTIES, ".*", 0, 10
        )
        assert len(props) == 1
        assert isinstance(props[0], domain.PropertyDeclaration)
        assert props[0].name == "p1"
        assert props[0].data_type == domain.PropertyDataType.STRING

        # Read telemetry
        telemetry = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.TELEMETRY, ".*", 0, 10
        )
        assert len(telemetry) == 1
        assert isinstance(telemetry[0], domain.TelemetryAttributeDeclaration)
        assert telemetry[0].name == "t1"

        # Read alerts
        alerts = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.ALERTS, ".*", 0, 10
        )
        assert len(alerts) == 1
        assert isinstance(alerts[0], domain.AlertDeclaration)
        assert alerts[0].name == "a1"
        assert alerts[0].severity == domain.AlertSeverity.WARNING

    async def test_get_historical_telemetry(self) -> None:
        historical = domain.HistoricalTelemetry(
            timestamps=[datetime.datetime.now()],
            values={"t1": [1.0]},
        )
        api = MockEnapterAPI(historical_telemetry=historical)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.get_historical_telemetry(
            auth,
            "dev-1",
            ["t1"],
            datetime.datetime.now(),
            datetime.datetime.now(),
            60,
        )

        assert result == historical