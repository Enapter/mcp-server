import datetime
from typing import Any, AsyncGenerator

import enapter
import pytest

from enapter_mcp_server import core, domain


def make_device_manifest(
    *,
    description: str | None = None,
    vendor: str | None = None,
    implements: list[str] | None = None,
    properties: dict[str, domain.PropertyDeclaration] | None = None,
    telemetry: dict[str, domain.TelemetryAttributeDeclaration] | None = None,
    alerts: dict[str, domain.AlertDeclaration] | None = None,
    commands: dict[str, domain.CommandDeclaration] | None = None,
) -> domain.DeviceManifest:
    return domain.DeviceManifest(
        description=description,
        vendor=vendor,
        implements=implements or [],
        properties=properties or {},
        telemetry=telemetry or {},
        alerts=alerts or {},
        commands=commands or {},
    )


def make_device(
    *,
    active_alerts: list[str] | None = None,
    manifest: domain.DeviceManifest | None = None,
    **kwargs: Any,
) -> domain.Device:
    return domain.Device(
        active_alerts=active_alerts,
        manifest=manifest,
        **kwargs,
    )


class MockEnapterAPI:
    def __init__(
        self,
        sites: list[domain.Site] | None = None,
        devices: list[domain.Device] | None = None,
        telemetry: dict[str, dict[str, Any]] | None = None,
        historical_telemetry: domain.HistoricalTelemetry | None = None,
        latest_telemetry_unavailable: bool = False,
        command_executions: dict[str, list[domain.CommandExecution]] | None = None,
        rule_engine_states: dict[str, domain.RuleEngine] | None = None,
        rules: dict[str, list[domain.Rule]] | None = None,
        execute_command_result: domain.CommandExecution | None = None,
        execute_command_raises: BaseException | None = None,
        create_rule_result: domain.Rule | None = None,
        create_rule_raises: BaseException | None = None,
        update_rule_script_result: domain.Rule | None = None,
        update_rule_script_raises: BaseException | None = None,
        delete_rule_raises: BaseException | None = None,
    ):
        self._sites = sites or []
        self._devices = devices or []
        self._telemetry = telemetry or {}
        self._historical_telemetry = historical_telemetry
        self._latest_telemetry_unavailable = latest_telemetry_unavailable
        self._command_executions = command_executions or {}
        self._rule_engine_states = rule_engine_states or {}
        self._rules = rules or {}
        self._execute_command_result = execute_command_result
        self._execute_command_raises = execute_command_raises
        self._create_rule_result = create_rule_result
        self._create_rule_raises = create_rule_raises
        self._update_rule_script_result = update_rule_script_result
        self._update_rule_script_raises = update_rule_script_raises
        self._delete_rule_raises = delete_rule_raises
        self.latest_telemetry_batch_calls = 0
        self.get_rule_engine_calls = 0
        self.execute_command_calls: list[dict[str, Any]] = []
        self.create_rule_calls: list[dict[str, Any]] = []
        self.update_rule_script_calls: list[dict[str, Any]] = []
        self.delete_rule_calls: list[dict[str, Any]] = []

    async def get_rule_engine(
        self, auth: core.AuthConfig, site_id: str
    ) -> domain.RuleEngine:
        import httpx

        self.get_rule_engine_calls += 1
        if site_id not in self._rule_engine_states:
            raise httpx.HTTPStatusError(
                "Not Found",
                request=httpx.Request("GET", f"/v3/sites/{site_id}/rule_engine"),
                response=httpx.Response(404, request=httpx.Request("GET", "")),
            )
        return self._rule_engine_states[site_id]

    @enapter.async_.generator
    async def list_rules(
        self, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[domain.Rule, None]:
        for rule in self._rules.get(site_id, []):
            yield rule

    async def get_rule(
        self, auth: core.AuthConfig, site_id: str, rule_id: str
    ) -> domain.Rule:
        for rule in self._rules.get(site_id, []):
            if rule.id == rule_id:
                return rule
        raise ValueError(f"Rule {rule_id} not found")

    @enapter.async_.generator
    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
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
        expand_active_alerts: bool = False,
    ) -> AsyncGenerator[domain.Device, None]:
        for d in self._devices:
            if site_id is not None and d.site_id != site_id:
                continue
            yield d

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
        all_executions = []
        for executions in self._command_executions.values():
            for execution in executions:
                if device_id is not None and execution.device_id != device_id:
                    continue
                if site_id is not None:
                    device = next(
                        (d for d in self._devices if d.id == execution.device_id), None
                    )
                    if device is None or device.site_id != site_id:
                        continue
                if created_at_gte is not None and execution.created_at < created_at_gte:
                    continue
                if created_at_lt is not None and execution.created_at >= created_at_lt:
                    continue
                if state is not None and execution.state != state:
                    continue
                all_executions.append(execution)

        all_executions.sort(key=lambda e: e.created_at, reverse=True)
        for execution in all_executions:
            yield execution

    async def get_device(
        self,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device:
        for device in self._devices:
            if device.id == device_id:
                return device
        raise ValueError(f"Device {device_id} not found")

    async def execute_command(
        self,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution:
        self.execute_command_calls.append(
            {
                "device_id": device_id,
                "command_name": command_name,
                "arguments": arguments,
            }
        )
        if self._execute_command_raises is not None:
            raise self._execute_command_raises
        if self._execute_command_result is None:
            raise NotImplementedError()
        return self._execute_command_result

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
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry:
        if self._historical_telemetry is None:
            raise NotImplementedError()
        return self._historical_telemetry

    async def create_rule(
        self,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule:
        self.create_rule_calls.append(
            {
                "site_id": site_id,
                "slug": slug,
                "script": script,
                "disabled": disabled,
            }
        )
        if self._create_rule_raises is not None:
            raise self._create_rule_raises
        if self._create_rule_result is None:
            raise NotImplementedError()
        return self._create_rule_result

    async def update_rule_script(
        self,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
        script: domain.RuleScript,
    ) -> domain.Rule:
        self.update_rule_script_calls.append(
            {
                "rule_id": rule_id,
                "site_id": site_id,
                "script": script,
            }
        )
        if self._update_rule_script_raises is not None:
            raise self._update_rule_script_raises
        if self._update_rule_script_result is None:
            raise NotImplementedError()
        return self._update_rule_script_result

    async def delete_rule(
        self, auth: core.AuthConfig, rule_id: str, site_id: str
    ) -> None:
        self.delete_rule_calls.append(
            {
                "rule_id": rule_id,
                "site_id": site_id,
            }
        )
        if self._delete_rule_raises is not None:
            raise self._delete_rule_raises
        return None


class TestApplicationServer:

    async def test_search_sites_filtering(self) -> None:
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="dev-1",
                name="Gateway 1",
                site_id="1",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            make_device(
                blueprint_id="bp-1",
                id="dev-2",
                name="Device 2",
                site_id="1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
            make_device(
                blueprint_id="bp-1",
                id="dev-3",
                name="Gateway 2",
                site_id="2",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
            make_device(
                blueprint_id="bp-1",
                id="dev-4",
                name="Device 4",
                site_id="3",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ]
        sites = [
            domain.Site(
                id="1",
                name="Alpha",
                timezone="Europe/Berlin",
                authorized_role=domain.AccessRole.OWNER,
            ),
            domain.Site(
                id="2",
                name="Beta",
                timezone="Europe/London",
                authorized_role=domain.AccessRole.USER,
            ),
            domain.Site(
                id="3",
                name="Gamma",
                timezone="Europe/Berlin",
                authorized_role=domain.AccessRole.OWNER,
            ),
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
            rule_engine_states={
                "1": domain.RuleEngine(
                    id="eng-1", state=domain.RuleEngineState.ACTIVE, timezone="UTC"
                ),
                "2": domain.RuleEngine(
                    id="eng-2", state=domain.RuleEngineState.SUSPENDED, timezone="UTC"
                ),
            },
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Test name filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_regexp="Alpha", timezone_regexp=".*"),
            offset=0,
            limit=20,
        )
        assert len(result) == 1
        assert result[0].name == "Alpha"
        assert result[0].authorized_role == domain.AccessRole.OWNER
        assert result[0].status is not None
        assert result[0].status.gateway_id == "dev-1"
        assert result[0].status.gateway_online is True
        assert result[0].status.devices_total == 2
        assert result[0].status.devices_online == 1
        assert result[0].status.rule_engine_state == domain.RuleEngineState.ACTIVE

        # Test site ID filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(
                site_id="2", name_regexp=".*", timezone_regexp=".*"
            ),
            offset=0,
            limit=20,
        )
        assert len(result) == 1
        assert result[0].id == "2"
        assert result[0].authorized_role == domain.AccessRole.USER
        assert result[0].status is not None
        assert result[0].status.rule_engine_state is None

        # Test timezone filtering
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_regexp=".*", timezone_regexp="Berlin"),
            offset=0,
            limit=20,
        )
        assert len(result) == 2
        assert result[0].name == "Alpha"
        assert result[0].status is not None
        assert result[0].status.rule_engine_state == domain.RuleEngineState.ACTIVE
        assert result[1].name == "Gamma"
        assert result[1].status is not None
        assert result[1].status.rule_engine_state is None

        # Test sorting and pagination
        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_regexp=".*", timezone_regexp=".*"),
            offset=0,
            limit=1,
        )
        assert len(result) == 1
        assert result[0].id == "1"
        assert result[0].status is not None
        assert result[0].status.devices_total == 2

    async def test_search_sites(self) -> None:
        site = domain.Site(
            id="site-1",
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="dev-1",
                name="Gateway",
                site_id="site-1",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            make_device(
                blueprint_id="bp-1",
                id="dev-2",
                name="Device 2",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
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
            rule_engine_states={
                "site-1": domain.RuleEngine(
                    id="eng-1", state=domain.RuleEngineState.ACTIVE, timezone="UTC"
                )
            },
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_regexp=".*", timezone_regexp=".*"),
            offset=0,
            limit=20,
        )

        assert len(result) == 1
        assert result[0].id == "site-1"
        assert result[0].authorized_role == domain.AccessRole.OWNER
        assert result[0].status is not None
        assert result[0].status.gateway_id == "dev-1"
        assert result[0].status.gateway_online is True
        assert result[0].status.devices_total == 2
        assert result[0].status.devices_online == 1
        assert result[0].status.rule_engine_state == domain.RuleEngineState.ACTIVE
        assert api.get_rule_engine_calls == 1

    async def test_search_sites_no_gateway_skips_rule_engine(self) -> None:
        site = domain.Site(
            id="site-1",
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="dev-1",
                name="Device 1",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ]
        api = MockEnapterAPI(
            sites=[site],
            devices=devices,
            rule_engine_states={
                "site-1": domain.RuleEngine(
                    id="eng-1", state=domain.RuleEngineState.ACTIVE, timezone="UTC"
                )
            },
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.search_sites(
            auth,
            query=core.SiteSearchQuery(name_regexp=".*", timezone_regexp=".*"),
            offset=0,
            limit=20,
        )

        assert len(result) == 1
        assert result[0].id == "site-1"
        assert result[0].status is not None
        assert result[0].status.gateway_id is None
        assert result[0].status.rule_engine_state is None
        assert api.get_rule_engine_calls == 0

    async def test_search_rules(self) -> None:
        gateway = make_device(
            blueprint_id="bp-1",
            id="gw-1",
            name="Gateway",
            site_id="site-1",
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )
        rules = [
            domain.Rule(
                id="rule-1",
                slug="alpha",
                disabled=False,
                state=domain.RuleState.STARTED,
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval="1m",
                    code="line 1\nline 2",
                ),
            ),
            domain.Rule(
                id="rule-2",
                slug="beta",
                disabled=True,
                state=domain.RuleState.STOPPED,
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V1,
                    exec_interval=None,
                    code="line 1",
                ),
            ),
        ]
        api = MockEnapterAPI(devices=[gateway], rules={"site-1": rules})
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Test listing all
        result = await app.search_rules(
            auth,
            query=core.RuleSearchQuery(site_id="site-1"),
            offset=0,
            limit=10,
        )
        assert len(result) == 2
        assert result[0].id == "rule-1"
        assert result[0].enabled is True
        assert result[0].script.summary.lines_count == 2
        assert result[1].id == "rule-2"
        assert result[1].enabled is False
        assert result[1].script.summary.lines_count == 1

        # Test slug filtering
        result = await app.search_rules(
            auth,
            query=core.RuleSearchQuery(site_id="site-1", slug_regexp="alpha"),
            offset=0,
            limit=10,
        )
        assert len(result) == 1
        assert result[0].slug == "alpha"

    async def test_read_rule(self) -> None:
        gateway = make_device(
            blueprint_id="bp-1",
            id="gw-1",
            name="Gateway",
            site_id="site-1",
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )
        rule = domain.Rule(
            id="rule-1",
            slug="test",
            disabled=False,
            state=domain.RuleState.STARTED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="line 1\nline 2\nline 3\nline 4",
            ),
        )
        api = MockEnapterAPI(devices=[gateway], rules={"site-1": [rule]})
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Read full
        result = await app.read_rule(auth, "site-1", "rule-1", offset=0, limit=10)
        assert result == ["line 1", "line 2", "line 3", "line 4"]

        # Read with pagination
        result = await app.read_rule(auth, "site-1", "rule-1", offset=1, limit=2)
        assert result == ["line 2", "line 3"]

    async def test_search_rules_gateway_absent(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.search_rules(
                auth,
                query=core.RuleSearchQuery(site_id="site-1"),
                offset=0,
                limit=10,
            )
        except core.GatewayUnavailable as exc:
            assert str(exc) == "The site has no gateway."
        else:
            raise AssertionError("Expected GatewayUnavailable")

    async def test_search_rules_gateway_offline(self) -> None:
        gateway = make_device(
            blueprint_id="bp-1",
            id="gw-1",
            name="Gateway",
            site_id="site-1",
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.OFFLINE,
        )
        api = MockEnapterAPI(devices=[gateway])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.search_rules(
                auth,
                query=core.RuleSearchQuery(site_id="site-1"),
                offset=0,
                limit=10,
            )
        except core.GatewayUnavailable as exc:
            assert str(exc) == "The site's gateway is currently offline."
        else:
            raise AssertionError("Expected GatewayUnavailable")

    async def test_search_devices(self) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
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
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                active_alerts=["a1"],
                manifest=manifest,
            ),
            make_device(
                blueprint_id="bp-1",
                id="2",
                name="Beta",
                site_id="s1",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                active_alerts=[],
                manifest=manifest,
            ),
            make_device(
                blueprint_id="bp-1",
                id="3",
                name="Gamma",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.OFFLINE,
                active_alerts=[],
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
                device_id=None, site_id="s1", device_type=None, name_regexp=".*"
            ),
            offset=0,
            limit=10,
            view=domain.DeviceViewType.BASIC,
        )
        assert len(result) == 2
        assert result[0].authorized_role == domain.AccessRole.OWNER
        assert result[0].connectivity == domain.ConnectivityStatus.ONLINE
        assert result[0].blueprint_summary is not None
        assert result[0].active_alerts_total == 1

        # Filter by type
        result = await app.search_devices(
            auth,
            query=core.DeviceSearchQuery(
                device_id=None,
                site_id=None,
                device_type=domain.DeviceType.GATEWAY,
                name_regexp=".*",
            ),
            offset=0,
            limit=10,
            view=domain.DeviceViewType.BASIC,
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
            view=domain.DeviceViewType.BASIC,
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
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                ),
                "p2": domain.PropertyDeclaration(
                    name="p2",
                    display_name="P2",
                    data_type=domain.DataType.STRING,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                ),
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
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
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1", "p2": "v2"},
                active_alerts=["a1"],
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(site_id="s1", name_regexp=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceViewType.FULL,
        )

        assert len(result) == 1
        assert result[0].authorized_role == domain.AccessRole.OWNER
        assert result[0].connectivity == domain.ConnectivityStatus.ONLINE
        assert result[0].blueprint_summary is not None
        assert isinstance(result[0], domain.DeviceViewFull)
        assert result[0].properties == {"p1": "v1", "p2": "v2"}
        assert result[0].active_alerts == ["a1"]
        assert result[0].active_alerts_total == 1

    async def test_search_devices_full_view_with_missing_alerts(self) -> None:
        manifest = make_device_manifest(
            description="Desc",
            vendor="Enapter",
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
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
            make_device(
                blueprint_id="bp-1",
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1"},
                active_alerts=[],
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(site_id="s1", name_regexp=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceViewType.FULL,
        )

        assert len(result) == 1
        assert isinstance(result[0], domain.DeviceViewFull)
        assert result[0].active_alerts == []
        assert result[0].active_alerts_total == 0

    async def test_search_devices_full_view_requires_site_or_device_id(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)

        try:
            await app.search_devices(
                core.AuthConfig(token="test"),
                query=core.DeviceSearchQuery(name_regexp=".*"),
                offset=0,
                limit=10,
                view=domain.DeviceViewType.FULL,
            )
        except core.SearchQueryTooBroad as exc:
            assert (
                str(exc)
                == "Please provide `site_id` or `device_id` to narrow down the search."
            )
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
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
            },
            telemetry={},
            alerts={},
            commands={},
        )
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="1",
                name="Alpha",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v1"},
                active_alerts=[],
                manifest=manifest,
            ),
            make_device(
                blueprint_id="bp-1",
                id="2",
                name="Beta",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
                properties={"p1": "v2"},
                active_alerts=[],
                manifest=manifest,
            ),
        ]
        api = MockEnapterAPI(devices=devices)
        app = core.ApplicationServer(api)

        result = await app.search_devices(
            core.AuthConfig(token="test"),
            query=core.DeviceSearchQuery(device_id="2", name_regexp=".*"),
            offset=0,
            limit=10,
            view=domain.DeviceViewType.FULL,
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
                    access_level=domain.AccessRole.READONLY,
                    description="D1",
                    enum=None,
                    unit=None,
                    implements=[],
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit="V",
                    implements=[],
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
                    access_level=domain.AccessRole.USER,
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
                    implements=[],
                )
            },
        )
        device = make_device(
            blueprint_id="bp-1",
            id="dev-1",
            name="Dev 1",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            authorized_role=domain.AccessRole.OWNER,
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

    async def test_read_blueprint_implements(self) -> None:
        manifest = make_device_manifest(
            implements=["energy.battery", "energy.inverter"]
        )
        device = make_device(
            blueprint_id="bp-1",
            id="dev-1",
            name="Dev 1",
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            authorized_role=domain.AccessRole.OWNER,
            manifest=manifest,
        )
        api = MockEnapterAPI(devices=[device])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Read implements
        implements = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.IMPLEMENTS, ".*", 0, 10
        )
        assert implements == ["energy.battery", "energy.inverter"]

        implements_filtered = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.IMPLEMENTS, "battery", 0, 10
        )
        assert implements_filtered == ["energy.battery"]

        # Read implements with pagination
        implements_paginated = await app.read_blueprint(
            auth, "dev-1", domain.BlueprintSection.IMPLEMENTS, ".*", 1, 1
        )
        assert implements_paginated == ["energy.inverter"]

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
            domain.AggregationFunction.AVG,
        )

        assert result == historical

    async def test_search_command_executions_by_state(self) -> None:
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="d1",
                name="D1",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
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
                ),
                domain.CommandExecution(
                    id="e2",
                    device_id="d1",
                    command_name="cmd2",
                    state=domain.CommandExecutionState.ERROR,
                    created_at=datetime.datetime(2023, 1, 2),
                ),
            ]
        }
        api = MockEnapterAPI(devices=devices, command_executions=executions)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        # Filter by SUCCESS
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(
                device_id="d1", state=domain.CommandExecutionState.SUCCESS
            ),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.BASIC,
        )
        assert len(result) == 1
        assert result[0].id == "e1"
        assert result[0].state == domain.CommandExecutionState.SUCCESS

        # Filter by ERROR
        result = await app.search_command_executions(
            auth,
            query=core.CommandExecutionSearchQuery(
                device_id="d1", state=domain.CommandExecutionState.ERROR
            ),
            offset=0,
            limit=10,
            view=domain.CommandExecutionView.BASIC,
        )
        assert len(result) == 1
        assert result[0].id == "e2"
        assert result[0].state == domain.CommandExecutionState.ERROR

    async def test_search_command_executions_basic(self) -> None:
        devices = [
            make_device(
                blueprint_id="bp-1",
                id="d1",
                name="D1",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
            ),
            make_device(
                blueprint_id="bp-1",
                id="d2",
                name="D2",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
            ),
            make_device(
                blueprint_id="bp-1",
                id="d3",
                name="D3",
                site_id="s2",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
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
            make_device(
                blueprint_id="bp-1",
                id="d1",
                name="D1",
                site_id="s1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
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
            assert (
                str(exc)
                == "Please provide `site_id` or `device_id` to narrow down the search."
            )
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
            assert str(exc) == "Please provide `device_id` to narrow down the search."
        else:
            raise AssertionError("Expected SearchQueryTooBroad")

    @staticmethod
    def _device_with_commands(
        device_id: str, commands: dict[str, domain.CommandDeclaration]
    ) -> domain.Device:
        return make_device(
            blueprint_id="bp-1",
            id=device_id,
            name=device_id,
            site_id="s1",
            type=domain.DeviceType.NATIVE,
            authorized_role=domain.AccessRole.OWNER,
            manifest=make_device_manifest(commands=commands),
        )

    async def test_execute_command_unknown_name_raises_and_not_called(self) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "reboot": domain.CommandDeclaration(
                    name="reboot",
                    display_name="Reboot",
                    access_level=domain.AccessRole.OWNER,
                    description=None,
                    arguments=[],
                    implements=[],
                ),
                "status": domain.CommandDeclaration(
                    name="status",
                    display_name="Status",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                ),
            },
        )
        api = MockEnapterAPI(devices=[device])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.execute_command(
                auth,
                device_id="dev-1",
                command_name="does_not_exist",
                arguments={},
            )
        except core.CommandNotFound as exc:
            message = str(exc)
            assert "does_not_exist" in message
            # The message must name an available command so the agent can
            # recover (correct a typo or hallucination).
            assert "reboot" in message
            assert "status" in message
        else:
            raise AssertionError("Expected CommandNotFound")

        # `execute` must NOT have been called when the name is unknown.
        assert api.execute_command_calls == []

    async def test_execute_command_confirmation_declared_flag_false_raises_and_not_called(
        self,
    ) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "reboot": domain.CommandDeclaration(
                    name="reboot",
                    display_name="Reboot",
                    access_level=domain.AccessRole.OWNER,
                    description=None,
                    arguments=[],
                    implements=[],
                    confirmation=domain.CommandConfirmation(
                        severity="warning",
                        title="Reboot the device",
                        description="This will restart the device.",
                    ),
                )
            },
        )
        api = MockEnapterAPI(devices=[device])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.execute_command(
                auth,
                device_id="dev-1",
                command_name="reboot",
                arguments={},
                human_confirmed_this_action=False,
            )
        except core.ConfirmationRequired as exc:
            message = str(exc)
            assert "Reboot the device" in message
            assert "This will restart the device." in message
        else:
            raise AssertionError("Expected ConfirmationRequired")

        # `execute` must NOT have been called on refusal.
        assert api.execute_command_calls == []

    async def test_execute_command_confirmation_declared_flag_true_proceeds(
        self,
    ) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "reboot": domain.CommandDeclaration(
                    name="reboot",
                    display_name="Reboot",
                    access_level=domain.AccessRole.OWNER,
                    description=None,
                    arguments=[],
                    implements=[],
                    confirmation=domain.CommandConfirmation(
                        severity="warning",
                        title="Reboot the device",
                        description="This will restart the device.",
                    ),
                )
            },
        )
        result = domain.CommandExecution(
            id="exec-1",
            device_id="dev-1",
            command_name="reboot",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2024, 1, 1),
            arguments={"x": 1},
            response_payload={"ok": True},
        )
        api = MockEnapterAPI(devices=[device], execute_command_result=result)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        out = await app.execute_command(
            auth,
            device_id="dev-1",
            command_name="reboot",
            arguments={"x": 1},
            human_confirmed_this_action=True,
        )

        assert out == result
        assert api.execute_command_calls == [
            {"device_id": "dev-1", "command_name": "reboot", "arguments": {"x": 1}}
        ]

    async def test_execute_command_no_confirmation_flag_false_proceeds(self) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "status": domain.CommandDeclaration(
                    name="status",
                    display_name="Status",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        result = domain.CommandExecution(
            id="exec-1",
            device_id="dev-1",
            command_name="status",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2024, 1, 1),
        )
        api = MockEnapterAPI(devices=[device], execute_command_result=result)
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        out = await app.execute_command(
            auth,
            device_id="dev-1",
            command_name="status",
            arguments={},
            human_confirmed_this_action=False,
        )

        assert out == result
        assert len(api.execute_command_calls) == 1

    async def test_execute_command_returns_command_execution_with_response_payload(
        self,
    ) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "status": domain.CommandDeclaration(
                    name="status",
                    display_name="Status",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        result = domain.CommandExecution(
            id="exec-1",
            device_id="dev-1",
            command_name="status",
            state=domain.CommandExecutionState.SUCCESS,
            created_at=datetime.datetime(2024, 1, 1),
            arguments={"a": 1},
            response_payload={"state": "running"},
        )
        api = MockEnapterAPI(devices=[device], execute_command_result=result)
        app = core.ApplicationServer(api)

        out = await app.execute_command(
            core.AuthConfig(token="test"),
            device_id="dev-1",
            command_name="status",
            arguments={"a": 1},
        )

        assert out.id == "exec-1"
        assert out.state == domain.CommandExecutionState.SUCCESS
        assert out.response_payload == {"state": "running"}

    @pytest.mark.parametrize(
        "state",
        [
            domain.CommandExecutionState.ERROR,
            domain.CommandExecutionState.TIMEOUT,
            domain.CommandExecutionState.UNSYNC,
        ],
    )
    async def test_execute_command_returns_terminal_states_without_raising(
        self, state: domain.CommandExecutionState
    ) -> None:
        device = self._device_with_commands(
            "dev-1",
            {
                "status": domain.CommandDeclaration(
                    name="status",
                    display_name="Status",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        result = domain.CommandExecution(
            id="exec-1",
            device_id="dev-1",
            command_name="status",
            state=state,
            created_at=datetime.datetime(2024, 1, 1),
        )
        api = MockEnapterAPI(devices=[device], execute_command_result=result)
        app = core.ApplicationServer(api)

        out = await app.execute_command(
            core.AuthConfig(token="test"),
            device_id="dev-1",
            command_name="status",
            arguments={},
        )

        assert out.state == state

    async def test_execute_command_sdk_raise_propagates(self) -> None:
        import httpx

        device = self._device_with_commands(
            "dev-1",
            {
                "status": domain.CommandDeclaration(
                    name="status",
                    display_name="Status",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                )
            },
        )
        api_error = httpx.HTTPStatusError(
            "Forbidden",
            request=httpx.Request(
                "POST", "https://api.enapter.com/v3/devices/dev-1/execute_command"
            ),
            response=httpx.Response(403, request=httpx.Request("POST", "")),
        )
        api = MockEnapterAPI(
            devices=[device],
            execute_command_result=None,
            execute_command_raises=api_error,
        )
        app = core.ApplicationServer(api)

        try:
            await app.execute_command(
                core.AuthConfig(token="test"),
                device_id="dev-1",
                command_name="status",
                arguments={},
            )
        except httpx.HTTPStatusError as exc:
            assert exc is api_error
        else:
            raise AssertionError("Expected the SDK exception to propagate")

    @staticmethod
    def _make_gateway(site_id: str = "site-1") -> domain.Device:
        return make_device(
            blueprint_id="bp-gw",
            id="gw-1",
            name="Gateway",
            site_id=site_id,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )

    @staticmethod
    def _make_rule(
        rule_id: str = "rule-1",
        slug: str = "mcp-test",
        disabled: bool = True,
        runtime_version: domain.RuleRuntimeVersion = domain.RuleRuntimeVersion.V3,
        exec_interval: str | None = None,
        script_code: str = "local x = 1\nreturn x",
    ) -> domain.Rule:
        return domain.Rule(
            id=rule_id,
            slug=slug,
            disabled=disabled,
            state=domain.RuleState.STOPPED,
            script=domain.RuleScript(
                runtime_version=runtime_version,
                exec_interval=exec_interval,
                code=script_code,
            ),
        )

    async def test_create_rule_rejects_unprefixed_slug(self) -> None:
        api = MockEnapterAPI(devices=[self._make_gateway()])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.create_rule(
                auth,
                "site-1",
                "my-rule",
                domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="code",
                ),
                disabled=True,
            )
        except domain.UnprefixedRuleSlug as exc:
            assert "my-rule" in str(exc)
            assert "mcp-" in str(exc)
        else:
            raise AssertionError("Expected UnprefixedRuleSlug")

        assert api.create_rule_calls == []

    async def test_create_rule_requires_gateway(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.create_rule(
                auth,
                "site-1",
                "mcp-test",
                domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="code",
                ),
                disabled=True,
            )
        except core.GatewayUnavailable:
            pass
        else:
            raise AssertionError("Expected GatewayUnavailable")

    async def test_create_rule_creates_disabled_v3(self) -> None:
        rule = self._make_rule()
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            create_rule_result=rule,
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.create_rule(
            auth,
            "site-1",
            "mcp-test",
            domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="local x = 1",
            ),
            disabled=True,
        )

        assert result.id == "rule-1"
        assert result.enabled is False
        assert result.script.summary.runtime_version == domain.RuleRuntimeVersion.V3
        assert len(api.create_rule_calls) == 1
        call = api.create_rule_calls[0]
        assert call["site_id"] == "site-1"
        assert call["slug"] == "mcp-test"
        assert call["script"].code == "local x = 1"
        assert call["script"].runtime_version == domain.RuleRuntimeVersion.V3
        assert call["disabled"] is True

    async def test_create_rule_rejects_enabled_rule(self) -> None:
        api = MockEnapterAPI(devices=[self._make_gateway()])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.create_rule(
                auth,
                "site-1",
                "mcp-test",
                domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="local x = 1",
                ),
                disabled=False,
            )
        except domain.RuleMustBeCreatedDisabled:
            pass
        else:
            raise AssertionError("Expected RuleMustBeCreatedDisabled")

        assert api.create_rule_calls == []

    async def test_edit_rule_gateway_offline(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "old", "new")
        except core.GatewayUnavailable:
            pass
        else:
            raise AssertionError("Expected GatewayUnavailable")

    async def test_edit_rule_empty_old_string(self) -> None:
        rule = self._make_rule(script_code="local x = 1")
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "", "new")
        except domain.EmptyRuleOldString:
            pass
        else:
            raise AssertionError("Expected EmptyRuleOldString")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_no_op(self) -> None:
        rule = self._make_rule(script_code="local x = 1")
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "same", "same")
        except domain.NoOpRuleEdit:
            pass
        else:
            raise AssertionError("Expected NoOpRuleEdit")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_enabled_rejected(self) -> None:
        rule = self._make_rule(disabled=False)
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "old", "new")
        except domain.RuleNotDisabled as exc:
            assert "rule-1" in str(exc)
        else:
            raise AssertionError("Expected RuleNotDisabled")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_unprefixed_slug_rejected(self) -> None:
        rule = self._make_rule(slug="my-rule", disabled=True)
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "old", "new")
        except domain.RuleNotMcpManaged:
            pass
        else:
            raise AssertionError("Expected RuleNotMcpManaged")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_non_v3_rejected(self) -> None:
        rule = self._make_rule(runtime_version=domain.RuleRuntimeVersion.V1)
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "old", "new")
        except domain.RuleNotV3:
            pass
        else:
            raise AssertionError("Expected RuleNotV3")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_no_match(self) -> None:
        rule = self._make_rule(script_code="local x = 1\nlocal y = 2")
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "absent_string", "new")
        except domain.RuleOldStringNotFound:
            pass
        else:
            raise AssertionError("Expected RuleOldStringNotFound")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_ambiguous_match(self) -> None:
        rule = self._make_rule(script_code="local x = 1\nlocal x = 2")
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "local x", "local y")
        except domain.AmbiguousRuleOldString as exc:
            assert "2" in str(exc)
        else:
            raise AssertionError("Expected AmbiguousRuleOldString")
        assert api.update_rule_script_calls == []

    async def test_edit_rule_no_op_before_match_count(self) -> None:
        rule = self._make_rule(script_code="local x = 1")
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.edit_rule(auth, "site-1", "rule-1", "local x", "local x")
        except domain.NoOpRuleEdit:
            pass
        else:
            raise AssertionError("Expected NoOpRuleEdit before match check")

    async def test_edit_rule_success_preserves_exec_interval(self) -> None:
        rule = self._make_rule(
            script_code="local x = 1\nlocal y = 2",
            exec_interval="2m",
        )
        updated = self._make_rule(
            script_code="local x = 99\nlocal y = 2",
            exec_interval="2m",
        )
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
            update_rule_script_result=updated,
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        result = await app.edit_rule(
            auth, "site-1", "rule-1", "local x = 1", "local x = 99"
        )

        assert result.id == "rule-1"
        assert len(api.update_rule_script_calls) == 1
        call = api.update_rule_script_calls[0]
        assert call["rule_id"] == "rule-1"
        assert call["site_id"] == "site-1"
        assert call["script"].code == "local x = 99\nlocal y = 2"
        assert call["script"].runtime_version == domain.RuleRuntimeVersion.V3
        assert call["script"].exec_interval == "2m"

    async def test_delete_rule_gateway_offline(self) -> None:
        api = MockEnapterAPI(devices=[])
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.delete_rule(auth, "site-1", "rule-1")
        except core.GatewayUnavailable:
            pass
        else:
            raise AssertionError("Expected GatewayUnavailable")

    async def test_delete_rule_enabled_rejected(self) -> None:
        rule = self._make_rule(disabled=False)
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.delete_rule(auth, "site-1", "rule-1")
        except domain.RuleNotDisabled:
            pass
        else:
            raise AssertionError("Expected RuleNotDisabled")

        assert api.delete_rule_calls == []

    async def test_delete_rule_unprefixed_slug_rejected(self) -> None:
        rule = self._make_rule(slug="my-rule", disabled=True)
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.delete_rule(auth, "site-1", "rule-1")
        except domain.RuleNotMcpManaged:
            pass
        else:
            raise AssertionError("Expected RuleNotMcpManaged")

        assert api.delete_rule_calls == []

    async def test_delete_rule_missing_rule_raises(self) -> None:
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        try:
            await app.delete_rule(auth, "site-1", "rule-missing")
        except ValueError:
            pass
        else:
            raise AssertionError("Expected error for missing rule")

        assert api.delete_rule_calls == []

    async def test_delete_rule_success(self) -> None:
        rule = self._make_rule()
        api = MockEnapterAPI(
            devices=[self._make_gateway()],
            rules={"site-1": [rule]},
        )
        app = core.ApplicationServer(api)
        auth = core.AuthConfig(token="test")

        await app.delete_rule(auth, "site-1", "rule-1")

        assert len(api.delete_rule_calls) == 1
        call = api.delete_rule_calls[0]
        assert call["rule_id"] == "rule-1"
        assert call["site_id"] == "site-1"
