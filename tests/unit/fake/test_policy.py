import datetime

import pytest

from enapter_mcp_server import core, domain, fake


def _make_rule(
    rule_id: str = "rule-1",
    slug: str = "alpha",
    disabled: bool = False,
    code: str = "local x = 1",
) -> domain.Rule:
    return domain.Rule(
        id=rule_id,
        slug=slug,
        disabled=disabled,
        state=domain.RuleState.STARTED if not disabled else domain.RuleState.STOPPED,
        script=domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval=None,
            code=code,
        ),
    )


def _make_state() -> fake.State:
    return fake.State(
        sites=[
            domain.Site(
                id="site-1",
                name="Site 1",
                timezone="UTC",
                authorized_role=domain.AccessRole.OWNER,
            ),
            domain.Site(
                id="site-2",
                name="Site 2",
                timezone="UTC",
                authorized_role=domain.AccessRole.USER,
            ),
        ],
        devices=[
            domain.Device(
                id="dev-1",
                blueprint_id="bp-1",
                name="Device 1",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            domain.Device(
                id="dev-2",
                blueprint_id="bp-1",
                name="Gateway",
                site_id="site-1",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
            domain.Device(
                id="dev-3",
                blueprint_id="bp-1",
                name="Device 3",
                site_id="site-2",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.OFFLINE,
            ),
        ],
        rule_engines=[
            domain.RuleEngine(
                id="site-1",
                state=domain.RuleEngineState.ACTIVE,
                timezone="UTC",
            ),
        ],
        rules=[_make_rule("rule-1", "alpha"), _make_rule("rule-2", "beta")],
        command_executions=[
            domain.CommandExecution(
                id="ce-1",
                device_id="dev-1",
                command_name="reboot",
                state=domain.CommandExecutionState.SUCCESS,
                created_at=datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
            ),
            domain.CommandExecution(
                id="ce-2",
                device_id="dev-2",
                command_name="ping",
                state=domain.CommandExecutionState.ERROR,
                created_at=datetime.datetime(2023, 1, 2, tzinfo=datetime.timezone.utc),
            ),
            domain.CommandExecution(
                id="ce-3",
                device_id="dev-3",
                command_name="reboot",
                state=domain.CommandExecutionState.SUCCESS,
                created_at=datetime.datetime(2023, 1, 3, tzinfo=datetime.timezone.utc),
            ),
        ],
    )


@pytest.fixture
def auth() -> core.AuthConfig:
    return core.AuthConfig(token="test-token", user="test-user")


@pytest.fixture
def policy() -> fake.DefaultPolicy:
    return fake.DefaultPolicy()


@pytest.fixture
def state() -> fake.State:
    return _make_state()


class TestListSites:
    async def test_yields_all_sites(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        sites = [s async for s in policy.list_sites(state, auth)]
        assert {s.id for s in sites} == {"site-1", "site-2"}

    async def test_empty_state(
        self, policy: fake.DefaultPolicy, auth: core.AuthConfig
    ) -> None:
        sites = [s async for s in policy.list_sites(fake.State(), auth)]
        assert sites == []


class TestListDevices:
    async def test_yields_all_devices(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        devices = [d async for d in policy.list_devices(state, auth)]
        assert {d.id for d in devices} == {"dev-1", "dev-2", "dev-3"}

    async def test_filtered_by_site_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        devices = [d async for d in policy.list_devices(state, auth, site_id="site-1")]
        assert {d.id for d in devices} == {"dev-1", "dev-2"}

    async def test_filtered_by_other_site(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        devices = [d async for d in policy.list_devices(state, auth, site_id="site-2")]
        assert {d.id for d in devices} == {"dev-3"}

    async def test_filtered_site_with_no_devices(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        devices = [d async for d in policy.list_devices(state, auth, site_id="site-x")]
        assert devices == []


class TestGetDevice:
    async def test_finds_by_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        device = await policy.get_device(state, auth, "dev-2")
        assert device.id == "dev-2"

    async def test_missing_raises_device_not_found(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.DeviceNotFound):
            await policy.get_device(state, auth, "dev-x")


class TestGetRuleEngine:
    async def test_finds_by_site_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        engine = await policy.get_rule_engine(state, auth, "site-1")
        assert engine.id == "site-1"
        assert engine.state == domain.RuleEngineState.ACTIVE

    async def test_missing_raises_rule_engine_not_found(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleEngineNotFound):
            await policy.get_rule_engine(state, auth, "site-x")


class TestListRules:
    async def test_yields_rules(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        rules = [r async for r in policy.list_rules(state, auth, "site-1")]
        assert {r.id for r in rules} == {"rule-1", "rule-2"}


class TestGetRule:
    async def test_finds_by_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        rule = await policy.get_rule(state, auth, "site-1", "rule-2")
        assert rule.id == "rule-2"
        assert rule.slug == "beta"

    async def test_finds_by_slug(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        rule = await policy.get_rule(state, auth, "site-1", "alpha")
        assert rule.id == "rule-1"

    async def test_missing_raises_rule_not_found(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleNotFound):
            await policy.get_rule(state, auth, "site-1", "rule-x")


class TestListCommandExecutions:
    async def test_yields_all_sorted_desc(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        executions = [e async for e in policy.list_command_executions(state, auth)]
        assert [e.id for e in executions] == ["ce-3", "ce-2", "ce-1"]

    async def test_filtered_by_device_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        executions = [
            e
            async for e in policy.list_command_executions(
                state, auth, device_id="dev-1"
            )
        ]
        assert [e.id for e in executions] == ["ce-1"]

    async def test_filtered_by_site_id(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        executions = [
            e
            async for e in policy.list_command_executions(state, auth, site_id="site-1")
        ]
        assert {e.id for e in executions} == {"ce-1", "ce-2"}

    async def test_filtered_by_state(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        executions = [
            e
            async for e in policy.list_command_executions(
                state, auth, execution_state=domain.CommandExecutionState.ERROR
            )
        ]
        assert [e.id for e in executions] == ["ce-2"]

    async def test_filtered_by_created_at_range(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        executions = [
            e
            async for e in policy.list_command_executions(
                state,
                auth,
                created_at_gte=datetime.datetime(
                    2023, 1, 2, tzinfo=datetime.timezone.utc
                ),
                created_at_lt=datetime.datetime(
                    2023, 1, 3, tzinfo=datetime.timezone.utc
                ),
            )
        ]
        assert [e.id for e in executions] == ["ce-2"]


class TestTelemetry:
    async def test_get_latest_telemetry_returns_empty(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        result = await policy.get_latest_telemetry(state, auth, {"dev-1": ["v"]})
        assert result == {}

    async def test_get_historical_telemetry_returns_empty(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        result = await policy.get_historical_telemetry(
            state,
            auth,
            "dev-1",
            ["v"],
            datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 1, 2, tzinfo=datetime.timezone.utc),
            60,
            domain.AggregationFunction.AVG,
        )
        assert result == domain.HistoricalTelemetry(timestamps=[], values={})


class TestReadWriteMethodsRaise:
    async def test_execute_command_raises(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await policy.execute_command(state, auth, "dev-1", "reboot", None)

    async def test_create_rule_raises(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await policy.create_rule(
                state,
                auth,
                "site-1",
                "slug",
                _make_rule().script,
                disabled=True,
            )

    async def test_update_rule_script_raises(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await policy.update_rule_script(
                state, auth, "rule-1", "site-1", _make_rule().script
            )

    async def test_delete_rule_raises(
        self, policy: fake.DefaultPolicy, state: fake.State, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await policy.delete_rule(state, auth, "rule-1", "site-1")
