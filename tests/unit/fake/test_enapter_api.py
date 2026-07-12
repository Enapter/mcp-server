import datetime

import pytest

from enapter_mcp_server import core, domain, fake

from . import _sample_policy


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
                id="dev-1",
                blueprint_id="bp-1",
                name="Device 1",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
                connectivity=domain.ConnectivityStatus.ONLINE,
            ),
        ],
    )


@pytest.fixture
def auth() -> core.AuthConfig:
    return core.AuthConfig(token="test-token", user="test-user")


class TestDispatcherDelegates:
    async def test_list_sites(self, auth: core.AuthConfig) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        async with api.list_sites(auth) as gen:
            sites = [s async for s in gen]
        assert [s.id for s in sites] == ["site-1"]

    async def test_list_devices_filtered_by_site(self, auth: core.AuthConfig) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        async with api.list_devices(auth, site_id="site-1") as gen:
            devices = [d async for d in gen]
        assert [d.id for d in devices] == ["dev-1"]

    async def test_get_device(self, auth: core.AuthConfig) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        device = await api.get_device(auth, "dev-1")
        assert device.id == "dev-1"

    async def test_get_device_missing_raises(self, auth: core.AuthConfig) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        with pytest.raises(core.DeviceNotFound):
            await api.get_device(auth, "dev-x")

    async def test_list_command_executions(self, auth: core.AuthConfig) -> None:
        state = fake.State(
            devices=[
                domain.Device(
                    id="dev-1",
                    blueprint_id="bp-1",
                    name="Device 1",
                    site_id="site-1",
                    type=domain.DeviceType.NATIVE,
                    authorized_role=domain.AccessRole.OWNER,
                ),
            ],
            command_executions=[
                domain.CommandExecution(
                    id="ce-1",
                    device_id="dev-1",
                    command_name="reboot",
                    state=domain.CommandExecutionState.SUCCESS,
                    created_at=datetime.datetime(
                        2023, 1, 1, tzinfo=datetime.timezone.utc
                    ),
                ),
            ],
        )
        api = fake.EnapterAPI(state=state, policy=fake.DefaultPolicy())
        async with api.list_command_executions(auth, device_id="dev-1") as gen:
            executions = [e async for e in gen]
        assert [e.id for e in executions] == ["ce-1"]

    async def test_read_write_raises_via_dispatcher(
        self, auth: core.AuthConfig
    ) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        with pytest.raises(NotImplementedError):
            await api.execute_command(auth, "dev-1", "reboot", None)


class TestFromUrl:
    def test_state_only_uses_default_policy(self) -> None:
        api = fake.EnapterAPI.from_url("fake://?state=tests.unit.fake._sample_state")
        assert isinstance(api.policy, fake.DefaultPolicy)
        assert api.state.sites[0].id == "site-1"

    def test_state_and_policy_uses_custom_policy(self) -> None:
        api = fake.EnapterAPI.from_url(
            "fake://?policy=tests.unit.fake._sample_policy"
            "&state=tests.unit.fake._sample_state"
        )
        assert type(api.policy) is _sample_policy.Policy
        assert isinstance(api.policy, fake.DefaultPolicy)

    def test_missing_state_raises(self) -> None:
        with pytest.raises(KeyError):
            fake.EnapterAPI.from_url("fake://?policy=tests.unit.fake._sample_policy")

    def test_fresh_state_independent_instances(self) -> None:
        api1 = fake.EnapterAPI.from_url("fake://?state=tests.unit.fake._sample_state")
        api2 = fake.EnapterAPI.from_url("fake://?state=tests.unit.fake._sample_state")
        assert api1.state is not api2.state

        api1.state.devices.append(
            domain.Device(
                id="dev-extra",
                blueprint_id="bp-1",
                name="Extra",
                site_id="site-1",
                type=domain.DeviceType.NATIVE,
                authorized_role=domain.AccessRole.OWNER,
            )
        )
        assert len(api1.state.devices) == 2
        assert len(api2.state.devices) == 1

    async def test_custom_policy_used_via_dispatcher(
        self, auth: core.AuthConfig
    ) -> None:
        api = fake.EnapterAPI.from_url(
            "fake://?policy=tests.unit.fake._sample_policy"
            "&state=tests.unit.fake._sample_state"
        )
        result = await api.execute_command(auth, "dev-1", "reboot", {"a": 1})
        assert result.id == "ce-fake"
        assert result.command_name == "reboot"
        assert result.arguments == {"a": 1}


class TestAsyncContextManager:
    async def test_context_manager_returns_self(self) -> None:
        api = fake.EnapterAPI(state=_make_state(), policy=fake.DefaultPolicy())
        async with api as ctx:
            assert ctx is api

    async def test_context_manager_from_url(self) -> None:
        async with fake.EnapterAPI.from_url(
            "fake://?state=tests.unit.fake._sample_state"
        ) as api:
            assert isinstance(api, fake.EnapterAPI)
