import datetime
from typing import Any, AsyncGenerator

import enapter

from enapter_mcp_server import core, domain


def make_device_manifest(
    *,
    description: str | None = None,
    vendor: str | None = None,
    properties: dict[str, domain.PropertyDeclaration] | None = None,
    telemetry: dict[str, domain.TelemetryAttributeDeclaration] | None = None,
    alerts: dict[str, domain.AlertDeclaration] | None = None,
    commands: dict[str, domain.CommandDeclaration] | None = None,
) -> domain.DeviceManifest:
    return domain.DeviceManifest(
        description=description,
        vendor=vendor,
        properties=properties or {},
        telemetry=telemetry or {},
        alerts=alerts or {},
        commands=commands or {},
    )


class MockEnapterAPI:
    def __init__(
        self,
        sites: list[core.SiteDTO] | None = None,
        devices: list[core.DeviceDTO] | None = None,
        telemetry: dict[str, dict[str, Any]] | None = None,
        historical_telemetry: domain.HistoricalTelemetry | None = None,
        latest_telemetry_unavailable: bool = False,
        command_executions: dict[str, list[domain.CommandExecution]] | None = None,
    ):
        self._sites = sites or []
        self._devices = devices or []
        self._telemetry = telemetry or {}
        self._historical_telemetry = historical_telemetry
        self._latest_telemetry_unavailable = latest_telemetry_unavailable
        self._command_executions = command_executions or {}
        self.latest_telemetry_batch_calls = 0

    @enapter.async_.generator
    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[core.SiteDTO, None]:
        for site in self._sites:
            yield site

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
    ) -> AsyncGenerator[core.DeviceDTO, None]:
        for d in self._devices:
            if site_id is None or d.site_id == site_id:
                yield d

    @enapter.async_.generator
    async def list_command_executions(
        self, auth: core.AuthConfig, device_id: str
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        for execution in self._command_executions.get(device_id, []):
            yield execution

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
        self, auth: core.AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]:
        self.latest_telemetry_batch_calls += 1
        if self._latest_telemetry_unavailable:
            raise core.LatestTelemetryUnavailable()
        return {
            device_id: self._telemetry.get(device_id, {})
            for device_id in attributes_by_device
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
        if self._historical_telemetry is None:
            raise NotImplementedError()
        return self._historical_telemetry


class TestApplicationServer:

    async def test_search_sites_filtering(self) -> None:
        devices = [
            core.DeviceDTO(
                id="dev-1",
                name="Gateway 1",
                site_id="1",
                type=domain.DeviceType.GATEWAY,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            core.DeviceDTO(
                id="dev-2",
                name="Device 2",
                site_id="1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
            core.DeviceDTO(
                id="dev-3",
                name="Gateway 2",
                site_id="2",
                type=domain.DeviceType.GATEWAY,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
            core.DeviceDTO(
                id="dev-4",
                name="Device 4",
                site_id="3",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ]
        sites = [
            core.SiteDTO(id="1", name="Alpha", timezone="Europe/Berlin"),
            core.SiteDTO(id="2", name="Beta", timezone="Europe/London"),
            core.SiteDTO(id="3", name="Gamma", timezone="Europe/Berlin"),
        ]
        api = MockEnapterAPI(
            sites=sites,
            devices=devices,
            telemetry={
                "dev-1": {"alerts": ["a1"]},
                "dev-2": {"alerts": []},
                "dev-3": {"alerts": ["a2", "a3"]},
                "dev-4": {"alerts": None},
            },
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Test name filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_pattern="Alpha", timezone_pattern=".*"),
            offset=0,
            limit=20,
        )
        assert len(result) == 1
        assert result[0].name == "Alpha"
        assert result[0].gateway_id == "dev-1"
        assert result[0].gateway_online is True
        assert result[0].devices_total == 2
        assert result[0].devices_online == 1

        # Test site ID filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(
                site_id="2", name_pattern=".*", timezone_pattern=".*"
            ),
            offset=0,
            limit=20,
        )
        assert len(result) == 1
        assert result[0].id == "2"

        # Test timezone filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_pattern=".*", timezone_pattern="Berlin"),
            offset=0,
            limit=20,
        )
        assert len(result) == 2
        assert result[0].name == "Alpha"
        assert result[1].name == "Gamma"

        # Test sorting and pagination
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_pattern=".*", timezone_pattern=".*"),
            offset=0,
            limit=1,
        )
        assert len(result) == 1
        assert result[0].id == "1"
        assert result[0].devices_total == 2

    async def test_search_sites(self) -> None:
        site = core.SiteDTO(id="site-1", name="Site 1", timezone="UTC")
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
        api = MockEnapterAPI(
            sites=[site],
            devices=devices,
            telemetry={
                "dev-1": {"alerts": ["a1"]},
                "dev-2": {"alerts": ["a2", "a3"]},
            },
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_pattern=".*", timezone_pattern=".*"),
            offset=0,
            limit=20,
        )

        assert len(result) == 1
        assert result[0].id == "site-1"
        assert result[0].gateway_id == "dev-1"
        assert result[0].gateway_online is True
        assert result[0].devices_total == 2
        assert result[0].devices_online == 1

    async def test_search_devices(self) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            alerts={
                "a1": domain.AlertDeclaration(
                    name="a1",
                    display_name="A1",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                )
            },
            commands={
                "c1": domain.CommandDeclaration(
                    name="c1",
                    display_name="C1",
                    description=None,
                    arguments=[],
                )
            },
        )
        devices = [
            core.DeviceDTO(
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                manifest=manifest,
            ),
            core.DeviceDTO(
                id="2",
                name="Beta",
                site_id="s1",
                type=domain.DeviceType.GATEWAY,
                connectivity=domain.ConnectivityStatus.ONLINE,
                manifest=manifest,
            ),
            core.DeviceDTO(
                id="3",
                name="Gamma",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.OFFLINE,
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Filter by site
        result = await app.search_devices(
            auth,
            query=core.DeviceSearchQuery(
                device_id=None, site_id="s1", device_type=None, name_pattern=".*"
            ),
            offset=0,
            limit=10,
            view=domain.DeviceView.BASIC,
        )
        assert len(result) == 2
        assert result[0].connectivity_status == domain.ConnectivityStatus.ONLINE
        assert result[0].blueprint_summary is not None
        assert result[0].properties is None
        assert result[0].active_alerts is None

        # Filter by type
        result = await app.search_devices(
            auth,
            query=core.DeviceSearchQuery(
                device_id=None,
                site_id=None,
                device_type=domain.DeviceType.GATEWAY,
                name_pattern=".*",
            ),
            offset=0,
            limit=10,
            view=domain.DeviceView.BASIC,
        )
        assert len(result) == 1
        assert result[0].id == "2"

        # Filter by connectivity status
        result = await app.search_devices(
            auth,
            query=core.DeviceSearchQuery(
                connectivity_status=domain.ConnectivityStatus.OFFLINE
            ),
            offset=0,
            limit=10,
            view=domain.DeviceView.BASIC,
        )
        assert len(result) == 1
        assert result[0].id == "3"

    async def test_search_devices_full_view(self) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                ),
                "p2": domain.PropertyDeclaration(
                    name="p2",
                    display_name="P2",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                ),
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            alerts={
                "a1": domain.AlertDeclaration(
                    name="a1",
                    display_name="A1",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                )
            },
            commands={
                "c1": domain.CommandDeclaration(
                    name="c1",
                    display_name="C1",
                    description=None,
                    arguments=[],
                )
            },
        )
        devices = [
            core.DeviceDTO(
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1", "p2": "v2", "extra": "ignored"},
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices, telemetry={"1": {"alerts": ["a1"]}})
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(site_id="s1", name_pattern=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceView.FULL,
        )

        assert len(result) == 1
        assert result[0].connectivity_status == domain.ConnectivityStatus.ONLINE
        assert result[0].blueprint_summary is not None
        assert result[0].properties == {"p1": "v1", "p2": "v2"}
        assert result[0].active_alerts == ["a1"]

    async def test_search_devices_full_view_with_missing_alerts(self) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            alerts={
                "a1": domain.AlertDeclaration(
                    name="a1",
                    display_name="A1",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                )
            },
        )
        devices = [
            core.DeviceDTO(
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1"},
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices, telemetry={"1": {}})
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(site_id="s1", name_pattern=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceView.FULL,
        )

        assert len(result) == 1
        assert result[0].active_alerts == []

    async def test_search_devices_full_view_with_unavailable_latest_telemetry(
        self,
    ) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            telemetry={},
            alerts={},
            commands={},
        )
        devices = [
            core.DeviceDTO(
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1"},
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(
            devices=devices,
            latest_telemetry_unavailable=True,
        )
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(site_id="s1", name_pattern=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceView.FULL,
        )

        assert len(result) == 1
        assert result[0].active_alerts == []

    async def test_search_devices_full_view_requires_site_or_device_id(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)

        try:
            await app.search_devices(
                core.AuthConfig(token="test"),
                query=core.DeviceSearchQuery(name_pattern=".*"),
                offset=0,
                limit=10,
                view=domain.DeviceView.FULL,
            )
        except core.SearchQueryTooBroad as exc:
            assert str(exc) == "FULL device search requires site_id or device_id"
            pass
        else:
            raise AssertionError("Expected SearchQueryTooBroad")

    async def test_search_devices_full_view_allows_device_id_without_site_id(
        self,
    ) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description=None,
                    enum=None,
                    unit=None,
                )
            },
            telemetry={},
            alerts={},
            commands={},
        )
        devices = [
            core.DeviceDTO(
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1"},
                manifest=manifest,
            ),
            core.DeviceDTO(
                id="2",
                name="Beta",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v2"},
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(device_id="2", name_pattern=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceView.FULL,
        )

        assert len(result) == 1
        assert result[0].id == "2"

    async def test_read_blueprint(self) -> None:
        manifest = make_device_manifest(
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    description="D1",
                    enum=None,
                    unit=None,
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    description=None,
                    enum=None,
                    unit="V",
                )
            },
            alerts={
                "a1": domain.AlertDeclaration(
                    name="a1",
                    display_name="A1",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                )
            },
            commands={
                "c1": domain.CommandDeclaration(
                    name="c1",
                    display_name="C1",
                    description="D1",
                    arguments=[
                        domain.CommandArgumentDeclaration(
                            name="a1",
                            display_name="A1",
                            data_type=domain.DataType.INTEGER,
                            required=True,
                            description=None,
                            enum=None,
                        )
                    ],
                )
            },
        )
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
        assert props[0].data_type == domain.DataType.STRING

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

        # Read commands
        commands = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.COMMANDS, ".*", 0, 10
        )
        assert len(commands) == 1
        assert isinstance(commands[0], domain.CommandDeclaration)
        assert commands[0].name == "c1"
        assert len(commands[0].arguments) == 1
        assert commands[0].arguments[0].name == "a1"
        assert commands[0].arguments[0].data_type == domain.DataType.INTEGER

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

    async def test_search_command_executions_basic(self) -> None:
        devices = [
            core.DeviceDTO(
                id="d1",
                name="D1",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
            ),
            core.DeviceDTO(
                id="d2",
                name="D2",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
            ),
            core.DeviceDTO(
                id="d3",
                name="D3",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
            ),
        ]
        executions = {
            "d1": [
                domain.CommandExecution(
                    id="e1",
                    device_id="d1",
                    command_name="cmd1",
                    state=domain.CommandExecutionState.SUCCESS,
                    created_at=datetime.datetime(2023, 1, 1),
                    arguments={"arg1": "val1"},
                    response_payload={"res1": "val1"},
                )
            ],
            "d2": [
                domain.CommandExecution(
                    id="e2",
                    device_id="d2",
                    command_name="cmd2",
                    state=domain.CommandExecutionState.ERROR,
                    created_at=datetime.datetime(2023, 1, 2),
                )
            ],
            "d3": [
                domain.CommandExecution(
                    id="e3",
                    device_id="d3",
                    command_name="cmd3",
                    state=domain.CommandExecutionState.SUCCESS,
                    created_at=datetime.datetime(2023, 1, 3),
                )
            ],
        }
        api = MockEnapterAPI(devices=devices, command_executions=executions)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # By site
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(site_id="s1"),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.BASIC,
        )
        assert len(result) == 2
        assert result[0].id == "e2"  # Sorted by created_at desc
        assert result[0].arguments is None
        assert result[0].response_payload is None
        assert result[1].id == "e1"
        assert result[1].arguments is None
        assert result[1].response_payload is None

        # By device and site, filtering
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(site_id="s1", device_id="d1"),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.BASIC,
        )
        assert len(result) == 1
        assert result[0].id == "e1"

        # By site and mismatching device
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(site_id="s1", device_id="d3"),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.BASIC,
        )
        assert len(result) == 0

    async def test_search_command_executions_full(self) -> None:
        devices = [
            core.DeviceDTO(
                id="d1",
                name="D1",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
            )
        ]
        executions = {
            "d1": [
                domain.CommandExecution(
                    id="e1",
                    device_id="d1",
                    command_name="cmd1",
                    state=domain.CommandExecutionState.SUCCESS,
                    created_at=datetime.datetime(2023, 1, 1),
                    arguments={"arg1": "val1"},
                    response_payload={"res1": "val1"},
                )
            ]
        }
        api = MockEnapterAPI(devices=devices, command_executions=executions)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(device_id="d1"),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.FULL,
        )
        assert len(result) == 1
        assert result[0].id == "e1"
        assert result[0].arguments == {"arg1": "val1"}
        assert result[0].response_payload == {"res1": "val1"}

        # Validate site_id scoping checks
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(site_id="s2", device_id="d1"),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.FULL,
        )
        assert len(result) == 0

    async def test_search_command_executions_requires_scope(self) -> None:
        api = MockEnapterAPI()
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.search_command_executions(
                auth,
                query=core.CommandExecutionSearchQuery(),
                offset=0,
                limit=10,
                view=domain.CommandExecutionView.BASIC,
            )
        except core.SearchQueryTooBroad as exc:
            assert str(exc) == "Command execution search requires site_id or device_id"
        else:
            raise AssertionError("Expected SearchQueryTooBroad")

        try:
            await app.search_command_executions(
                auth,
                query=core.CommandExecutionSearchQuery(site_id="s1"),
                offset=0,
                limit=10,
                view=domain.CommandExecutionView.FULL,
            )
        except core.SearchQueryTooBroad as exc:
            assert str(exc) == "FULL command execution search requires device_id"
        else:
            raise AssertionError("Expected SearchQueryTooBroad")
