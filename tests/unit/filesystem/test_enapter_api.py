import pathlib
import tempfile
from typing import AsyncGenerator, Generator

import pytest
import yaml

from enapter_mcp_server import core, domain, filesystem

INVALID_ID = "../etc"

SITE_1 = "11111111-1111-1111-1111-111111111111"
SITE_2 = "22222222-2222-2222-2222-222222222222"
SITE_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEV_1 = "ddddddd1-1111-1111-1111-111111111111"
DEV_2 = "ddddddd2-2222-2222-2222-222222222222"
DEV_NX = "99999999-9999-9999-9999-999999999999"


@pytest.fixture
def auth() -> core.AuthConfig:
    return core.AuthConfig(token="test-token", user="test-user")


@pytest.fixture
def state_dir() -> Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.fixture
async def api(
    state_dir: pathlib.Path,
) -> AsyncGenerator[filesystem.EnapterAPI, None]:
    async with filesystem.EnapterAPI(state_dir) as a:
        yield a


def _dump_yaml(data: object) -> str:
    return yaml.dump(
        data, sort_keys=False, allow_unicode=True, default_flow_style=False
    )


def _write_site_file(
    state_dir: pathlib.Path,
    site_domain: domain.Site,
    devices_domain: list[domain.Device] | None = None,
) -> None:
    site_model = filesystem.models.Site.from_domain(site_domain)
    device_models = [
        filesystem.models.Device.from_domain(d) for d in (devices_domain or [])
    ]
    file_model = filesystem.models.SiteAggregate(site=site_model, devices=device_models)
    data = file_model.model_dump(mode="json", exclude_none=True)
    path = state_dir / "sites" / f"{site_domain.id}.yaml"
    filesystem.EnapterAPI(state_dir)._atomic_write(path, _dump_yaml(data))


def _write_rule_engine_file(
    state_dir: pathlib.Path,
    engine_domain: domain.RuleEngine,
    rules_domain: list[domain.Rule] | None = None,
) -> None:
    engine_model = filesystem.models.RuleEngine.from_domain(engine_domain)
    rule_models = [filesystem.models.Rule.from_domain(r) for r in (rules_domain or [])]
    file_model = filesystem.models.RuleEngineAggregate(
        rule_engine=engine_model, rules=rule_models
    )
    data = file_model.model_dump(mode="json", exclude_none=True)
    path = state_dir / "rule_engines" / f"{engine_domain.id}.yaml"
    filesystem.EnapterAPI(state_dir)._atomic_write(path, _dump_yaml(data))


def _make_script(code: str = "local x = 1", **kwargs: object) -> domain.RuleScript:
    defaults: dict[str, object] = {
        "runtime_version": domain.RuleRuntimeVersion.V3,
        "exec_interval": None,
        "code": code,
    }
    defaults.update(kwargs)
    return domain.RuleScript(**defaults)  # type: ignore[arg-type]


def _make_rule(
    rule_id: str = "fffffff1-1111-1111-1111-111111111111",
    slug: str = "test-rule",
    disabled: bool = True,
    script: domain.RuleScript | None = None,
) -> domain.Rule:
    if script is None:
        script = _make_script()
    return domain.Rule(
        id=rule_id,
        slug=slug,
        disabled=disabled,
        state=domain.RuleState.STARTED if not disabled else domain.RuleState.STOPPED,
        script=script,
    )


class TestListSites:
    async def test_empty(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        async with api.list_sites(auth) as gen:
            sites = [s async for s in gen]
        assert sites == []

    async def test_single(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        site = domain.Site(
            id=SITE_1,
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        _write_site_file(state_dir, site)

        async with api.list_sites(auth) as gen:
            sites = [s async for s in gen]
        assert len(sites) == 1
        assert sites[0] == site

    async def test_multiple(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        site1 = domain.Site(
            id=SITE_A,
            name="Site A",
            timezone="UTC",
            authorized_role=domain.AccessRole.USER,
        )
        site2 = domain.Site(
            id=SITE_B,
            name="Site B",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        _write_site_file(state_dir, site1)
        _write_site_file(state_dir, site2)

        async with api.list_sites(auth) as gen:
            sites = [s async for s in gen]
        assert len(sites) == 2
        assert {s.id for s in sites} == {SITE_A, SITE_B}


class TestGetRuleEngine:
    async def test_returns_engine(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)

        result = await api.get_rule_engine(auth, SITE_1)
        assert result == engine

    async def test_missing_raises_rule_engine_not_found(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleEngineNotFound):
            await api.get_rule_engine(auth, DEV_NX)

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.get_rule_engine(auth, INVALID_ID)


class TestListRules:
    async def test_empty(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        async with api.list_rules(auth, SITE_1) as gen:
            rules = [r async for r in gen]
        assert rules == []

    async def test_rules_in_file(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule1 = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111", slug="rule-1"
        )
        rule2 = _make_rule(
            rule_id="fffffff2-2222-2222-2222-222222222222", slug="rule-2"
        )
        _write_rule_engine_file(state_dir, engine, [rule1, rule2])

        async with api.list_rules(auth, SITE_1) as gen:
            rules = [r async for r in gen]
        assert len(rules) == 2
        assert {r.id for r in rules} == {rule1.id, rule2.id}

    async def test_no_file_returns_empty(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        async with api.list_rules(auth, DEV_NX) as gen:
            rules = [r async for r in gen]
        assert rules == []

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            async with api.list_rules(auth, INVALID_ID) as gen:
                async for _ in gen:
                    pass


class TestGetRule:
    async def test_returns_rule(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111", slug="get-test"
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        result = await api.get_rule(auth, SITE_1, rule.id)
        assert result == rule

    async def test_finds_by_slug(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111", slug="slug-lookup"
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        result = await api.get_rule(auth, SITE_1, "slug-lookup")
        assert result == rule

    async def test_missing_raises_rule_not_found(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(rule_id="fffffff1-1111-1111-1111-111111111111", slug="exists")
        _write_rule_engine_file(state_dir, engine, [rule])

        with pytest.raises(core.RuleNotFound):
            await api.get_rule(auth, SITE_1, DEV_NX)

    async def test_missing_file_raises_rule_engine_not_found(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleEngineNotFound):
            await api.get_rule(auth, SITE_1, DEV_NX)

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.get_rule(auth, INVALID_ID, DEV_NX)

    async def test_invalid_rule_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.get_rule(auth, SITE_1, INVALID_ID)


class TestListDevices:
    async def test_empty(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        async with api.list_devices(auth) as gen:
            devices = [d async for d in gen]
        assert devices == []

    async def test_with_site_id(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        site = domain.Site(
            id=SITE_1,
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        dev1 = domain.Device(
            id=DEV_1,
            blueprint_id="bp-1",
            name="Device 1",
            site_id=SITE_1,
            type=domain.DeviceType.LUA,
            authorized_role=domain.AccessRole.OWNER,
        )
        dev2 = domain.Device(
            id=DEV_2,
            blueprint_id="bp-2",
            name="Device 2",
            site_id=SITE_1,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
        )
        _write_site_file(state_dir, site, [dev1, dev2])

        async with api.list_devices(auth, site_id=SITE_1) as gen:
            devices = [d async for d in gen]
        assert len(devices) == 2
        assert {d.id for d in devices} == {DEV_1, DEV_2}

    async def test_without_site_id(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        site1 = domain.Site(
            id=SITE_1,
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        dev1 = domain.Device(
            id=DEV_1,
            blueprint_id="bp-1",
            name="Device 1",
            site_id=SITE_1,
            type=domain.DeviceType.LUA,
            authorized_role=domain.AccessRole.OWNER,
        )
        site2 = domain.Site(
            id=SITE_2,
            name="Site 2",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        dev2 = domain.Device(
            id=DEV_2,
            blueprint_id="bp-2",
            name="Device 2",
            site_id=SITE_2,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.OWNER,
        )
        _write_site_file(state_dir, site1, [dev1])
        _write_site_file(state_dir, site2, [dev2])

        async with api.list_devices(auth) as gen:
            devices = [d async for d in gen]
        assert len(devices) == 2
        assert {d.id for d in devices} == {DEV_1, DEV_2}

    async def test_empty_no_files(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        async with api.list_devices(auth) as gen:
            devices = [d async for d in gen]
        assert devices == []

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            async with api.list_devices(auth, site_id=INVALID_ID) as gen:
                async for _ in gen:
                    pass


class TestGetDevice:
    async def test_returns_device(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        site = domain.Site(
            id=SITE_1,
            name="Site 1",
            timezone="UTC",
            authorized_role=domain.AccessRole.OWNER,
        )
        device = domain.Device(
            id=DEV_1,
            blueprint_id="bp-1",
            name="Device 1",
            site_id=SITE_1,
            type=domain.DeviceType.GATEWAY,
            authorized_role=domain.AccessRole.SYSTEM,
            connectivity=domain.ConnectivityStatus.ONLINE,
        )
        _write_site_file(state_dir, site, [device])

        result = await api.get_device(auth, DEV_1)
        assert result == device

    async def test_finds_by_slug(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        model = filesystem.models.Site.from_domain(
            domain.Site(
                id=SITE_1,
                name="Site 1",
                timezone="UTC",
                authorized_role=domain.AccessRole.OWNER,
            )
        )
        dev_model = filesystem.models.Device(
            id=DEV_1,
            blueprint_id="bp-1",
            name="Device 1",
            site_id=SITE_1,
            type="lua",
            authorized_role="owner",
            slug="my-device",
        )
        agg = filesystem.models.SiteAggregate(site=model, devices=[dev_model])
        data = agg.model_dump(mode="json", exclude_none=True)
        path = state_dir / "sites" / f"{SITE_1}.yaml"
        filesystem.EnapterAPI(state_dir)._atomic_write(path, _dump_yaml(data))

        result = await api.get_device(auth, "my-device")
        assert result.id == DEV_1

    async def test_missing_raises_device_not_found(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.DeviceNotFound):
            await api.get_device(auth, DEV_NX)

    async def test_invalid_device_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.get_device(auth, INVALID_ID)


class TestCreateRule:
    async def test_creates_rule_stopped_when_disabled(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)
        script = domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval="10s",
            code='log("testing")',
        )
        rule = await api.create_rule(
            auth,
            site_id=SITE_1,
            slug="my-rule",
            script=script,
            disabled=True,
        )

        assert rule.id
        assert rule.slug == "my-rule"
        assert rule.disabled is True
        assert rule.state == domain.RuleState.STOPPED
        assert rule.script == script

    async def test_creates_rule_started_when_not_disabled(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)
        script = _make_script('log("enabled")')
        rule = await api.create_rule(
            auth, site_id=SITE_1, slug="enabled-rule", script=script, disabled=False
        )

        assert rule.disabled is False
        assert rule.state == domain.RuleState.STARTED

    async def test_writes_to_rule_engine_file(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)
        script = _make_script()
        rule = await api.create_rule(
            auth,
            site_id=SITE_1,
            slug="file-test",
            script=script,
            disabled=True,
        )

        path = state_dir / "rule_engines" / f"{SITE_1}.yaml"
        data = yaml.safe_load(path.read_text())
        rules = data["rules"]
        assert len(rules) == 1
        assert rules[0]["id"] == rule.id
        assert rules[0]["slug"] == "file-test"
        assert rules[0]["disabled"] is True
        assert rules[0]["state"] == "stopped"

    async def test_slug_conflict_raises(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        existing = _make_rule(slug="duplicate-slug")
        _write_rule_engine_file(state_dir, engine, [existing])

        with pytest.raises(core.RuleSlugConflict) as exc_info:
            await api.create_rule(
                auth,
                site_id=SITE_1,
                slug="duplicate-slug",
                script=_make_script("other"),
                disabled=True,
            )
        assert exc_info.value.slug == "duplicate-slug"
        assert exc_info.value.site_id == SITE_1

    async def test_same_slug_different_site_ok(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine1 = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine1)
        engine2 = domain.RuleEngine(
            id=SITE_2,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine2)

        script = _make_script()
        r1 = await api.create_rule(
            auth, site_id=SITE_1, slug="shared-slug", script=script, disabled=True
        )
        r2 = await api.create_rule(
            auth, site_id=SITE_2, slug="shared-slug", script=script, disabled=True
        )
        assert r1.id != r2.id

    async def test_rule_engine_file_missing_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleEngineNotFound):
            await api.create_rule(
                auth,
                site_id=SITE_1,
                slug="test",
                script=_make_script(),
                disabled=True,
            )

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.create_rule(
                auth,
                site_id=INVALID_ID,
                slug="test",
                script=_make_script(),
                disabled=True,
            )


class TestUpdateRuleScript:
    async def test_updates_script(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111",
            slug="update-test",
            script=_make_script("local a = 1"),
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        new_script = domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval="30s",
            code="local b = 2",
        )
        updated = await api.update_rule_script(auth, rule.id, SITE_1, new_script)

        assert updated.id == rule.id
        assert updated.slug == rule.slug
        assert updated.script == new_script

    async def test_updates_by_slug(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111",
            slug="update-slug",
            script=_make_script("old code"),
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        new_script = domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval=None,
            code="new code",
        )
        updated = await api.update_rule_script(auth, "update-slug", SITE_1, new_script)
        assert updated.script == new_script
        assert updated.id == rule.id

    async def test_file_is_rewritten(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111",
            slug="rewrite-test",
            script=_make_script("old"),
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        new_script = domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V1,
            exec_interval="5s",
            code="new",
        )
        await api.update_rule_script(auth, rule.id, SITE_1, new_script)

        path = state_dir / "rule_engines" / f"{SITE_1}.yaml"
        data = yaml.safe_load(path.read_text())
        rules = data["rules"]
        assert rules[0]["script"]["code"] == "new"
        assert rules[0]["script"]["runtime_version"] == "v1"
        assert rules[0]["script"]["exec_interval"] == "5s"

    async def test_missing_rule_raises_rule_not_found(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)

        script = _make_script()
        with pytest.raises(core.RuleNotFound):
            await api.update_rule_script(auth, DEV_NX, SITE_1, script)

    async def test_missing_file_raises_rule_engine_not_found(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        script = _make_script()
        with pytest.raises(core.RuleEngineNotFound):
            await api.update_rule_script(auth, DEV_NX, SITE_1, script)

    async def test_invalid_rule_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.update_rule_script(auth, INVALID_ID, SITE_1, _make_script())

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.update_rule_script(auth, DEV_NX, INVALID_ID, _make_script())


class TestDeleteRule:
    async def test_removes_from_file(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111", slug="delete-test"
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        await api.delete_rule(auth, rule.id, SITE_1)

        path = state_dir / "rule_engines" / f"{SITE_1}.yaml"
        data = yaml.safe_load(path.read_text())
        assert data["rules"] == []

    async def test_deletes_by_slug(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule = _make_rule(
            rule_id="fffffff1-1111-1111-1111-111111111111", slug="delete-slug"
        )
        _write_rule_engine_file(state_dir, engine, [rule])

        await api.delete_rule(auth, "delete-slug", SITE_1)

        async with api.list_rules(auth, SITE_1) as gen:
            rules = [r async for r in gen]
        assert rules == []

    async def test_deleted_rule_not_listed(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule1 = _make_rule(rule_id="fffffff1-1111-1111-1111-111111111111", slug="keep")
        rule2 = _make_rule(
            rule_id="fffffff2-2222-2222-2222-222222222222", slug="vanish"
        )
        _write_rule_engine_file(state_dir, engine, [rule1, rule2])

        await api.delete_rule(auth, rule2.id, SITE_1)

        async with api.list_rules(auth, SITE_1) as gen:
            rules = [r async for r in gen]
        assert len(rules) == 1
        assert rules[0].id == rule1.id

    async def test_missing_raises_rule_not_found(
        self,
        api: filesystem.EnapterAPI,
        auth: core.AuthConfig,
        state_dir: pathlib.Path,
    ) -> None:
        engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        _write_rule_engine_file(state_dir, engine)

        with pytest.raises(core.RuleNotFound):
            await api.delete_rule(auth, DEV_NX, SITE_1)

    async def test_missing_file_raises_rule_engine_not_found(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(core.RuleEngineNotFound):
            await api.delete_rule(auth, DEV_NX, SITE_1)

    async def test_invalid_rule_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.delete_rule(auth, INVALID_ID, SITE_1)

    async def test_invalid_site_id_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            await api.delete_rule(auth, DEV_NX, INVALID_ID)


class TestValidateId:
    def test_valid_uuid_does_not_raise(self, api: filesystem.EnapterAPI) -> None:
        api._validate_id(SITE_1)

    def test_valid_slug_does_not_raise(self, api: filesystem.EnapterAPI) -> None:
        api._validate_id("my-device")

    def test_invalid_slash_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("foo/bar")

    def test_invalid_dot_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("foo.bar")

    def test_invalid_parent_dir_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("../etc")

    def test_invalid_leading_dash_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("-foo")

    def test_invalid_trailing_dash_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("foo-")

    def test_invalid_empty_raises(self, api: filesystem.EnapterAPI) -> None:
        with pytest.raises(ValueError, match="Invalid ID"):
            api._validate_id("")


class TestUnimplementedMethods:
    async def test_execute_command_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await api.execute_command(auth, DEV_1, "cmd", None)

    async def test_get_latest_telemetry_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            await api.get_latest_telemetry(auth, {})

    async def test_get_historical_telemetry_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        import datetime

        with pytest.raises(NotImplementedError):
            await api.get_historical_telemetry(
                auth,
                device_id=DEV_1,
                attributes=[],
                time_from=datetime.datetime.now(),
                time_to=datetime.datetime.now(),
                granularity=60,
                aggregation=domain.AggregationFunction.AVG,
            )

    async def test_list_command_executions_raises(
        self, api: filesystem.EnapterAPI, auth: core.AuthConfig
    ) -> None:
        with pytest.raises(NotImplementedError):
            async with api.list_command_executions(auth) as gen:
                async for _ in gen:
                    pass


class TestAsyncContextManager:
    async def test_context_manager_works(self, state_dir: pathlib.Path) -> None:
        async with filesystem.EnapterAPI(state_dir) as api:
            assert isinstance(api, filesystem.EnapterAPI)
            assert api._state_dir == state_dir


class TestFromUrl:
    def test_absolute_path(self) -> None:
        api = filesystem.EnapterAPI.from_url("filetree:///tmp/state")
        assert api._state_dir == pathlib.Path("/tmp/state")

    def test_no_path_raises(self) -> None:
        with pytest.raises(ValueError, match="absolute path"):
            filesystem.EnapterAPI.from_url("filetree://")

    def test_relative_path_raises(self) -> None:
        with pytest.raises(ValueError, match="absolute path"):
            filesystem.EnapterAPI.from_url("filetree:relative/state")

    def test_with_host_raises(self) -> None:
        with pytest.raises(ValueError, match="must not have a host"):
            filesystem.EnapterAPI.from_url("filetree://localhost/state")
