import pytest

from enapter_mcp_server import core, domain, fake
from tests.agent.policies.create_rule import Policy


def _make_script(code: str = "local x = 1") -> domain.RuleScript:
    return domain.RuleScript(
        runtime_version=domain.RuleRuntimeVersion.V3,
        exec_interval=None,
        code=code,
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
        ],
        devices=[
            domain.Device(
                id="gw-1",
                blueprint_id="bp-1",
                name="Gateway",
                site_id="site-1",
                type=domain.DeviceType.GATEWAY,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ],
        rule_engines=[
            domain.RuleEngine(
                id="site-1",
                state=domain.RuleEngineState.ACTIVE,
                timezone="UTC",
            ),
        ],
        rules=[],
        command_executions=[],
    )


@pytest.fixture
def policy() -> Policy:
    return Policy()


@pytest.fixture
def auth() -> core.AuthConfig:
    return core.AuthConfig(token="test-token", user="test-user")


class TestCreateRule:
    async def test_appends_rule_to_state(
        self, policy: Policy, auth: core.AuthConfig
    ) -> None:
        state = _make_state()
        script = _make_script("scheduler.add(60, check_offline)")
        rule = await policy.create_rule(
            state, auth, "site-1", "enapter:check-offline", script, disabled=True
        )
        assert len(state.rules) == 1
        assert state.rules[0] is rule

    async def test_disabled_rule_is_stopped(
        self, policy: Policy, auth: core.AuthConfig
    ) -> None:
        state = _make_state()
        script = _make_script()
        rule = await policy.create_rule(
            state, auth, "site-1", "myrule", script, disabled=True
        )
        assert rule.disabled is True
        assert rule.state == domain.RuleState.STOPPED

    async def test_enabled_rule_is_started(
        self, policy: Policy, auth: core.AuthConfig
    ) -> None:
        state = _make_state()
        script = _make_script()
        rule = await policy.create_rule(
            state, auth, "site-1", "myrule", script, disabled=False
        )
        assert rule.disabled is False
        assert rule.state == domain.RuleState.STARTED

    async def test_enforces_slug_uniqueness(
        self, policy: Policy, auth: core.AuthConfig
    ) -> None:
        state = _make_state()
        script = _make_script()
        await policy.create_rule(
            state, auth, "site-1", "dup-slug", script, disabled=True
        )
        with pytest.raises(core.RuleSlugConflict):
            await policy.create_rule(
                state, auth, "site-1", "dup-slug", script, disabled=True
            )

    async def test_generates_id(self, policy: Policy, auth: core.AuthConfig) -> None:
        state = _make_state()
        script = _make_script()
        rule = await policy.create_rule(
            state, auth, "site-1", "rule-a", script, disabled=True
        )
        assert rule.id
        assert isinstance(rule.id, str)
        assert len(rule.id) == 32
