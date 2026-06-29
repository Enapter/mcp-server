import contextlib
import datetime
from typing import Any, AsyncGenerator, Callable, Coroutine, cast

import enapter
import pytest

from enapter_mcp_server import core, domain, http


class FailingTelemetryClient:
    async def latest(
        self, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, enapter.http.api.telemetry.LatestDatapoint | None]]:
        raise enapter.http.api.Error(
            message="broken device",
            code="bad_device",
            details={"device_id": "dev-1"},
        )


class FakeClient:
    def __init__(self) -> None:
        self.telemetry = FailingTelemetryClient()


class StubEnapterAPI(http.EnapterAPI):
    @contextlib.asynccontextmanager
    async def _new_client(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[enapter.http.api.Client, None]:
        yield cast(enapter.http.api.Client, FakeClient())


class TestEnapterAPI:
    async def test_get_latest_telemetry_raises_latest_telemetry_unavailable(
        self,
    ) -> None:
        api = StubEnapterAPI(base_url="http://example.test")

        try:
            await api.get_latest_telemetry(
                core.AuthConfig(token="test"),
                {"dev-1": ["alerts"]},
            )
        except core.LatestTelemetryUnavailable:
            pass
        else:
            raise AssertionError("Expected LatestTelemetryUnavailable")


# ---------------------------------------------------------------------------
#  Fakes for execute_command tests
# ---------------------------------------------------------------------------

_SdkExecuteFn = (
    Callable[
        [str, str, dict[str, Any] | None],
        Coroutine[None, None, enapter.http.api.commands.Execution],
    ]
    | None
)


class _SpyCommandsClient:
    """Records calls to `execute` and returns a pre-configured result or raises."""

    def __init__(
        self,
        *,
        result: enapter.http.api.commands.Execution | None = None,
        raises: Exception | None = None,
        side_effect: _SdkExecuteFn = None,
    ) -> None:
        self.result = result
        self.raises = raises
        self.side_effect = side_effect
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def execute(
        self,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> enapter.http.api.commands.Execution:
        self.calls.append((device_id, command_name, arguments))
        if self.side_effect is not None:
            return await self.side_effect(device_id, command_name, arguments)
        if self.raises is not None:
            raise self.raises
        if self.result is not None:
            return self.result
        raise NotImplementedError("No result, raises, or side_effect configured")


class _CommandFakeClient:
    """Fake SDK Client exposing only `commands`."""

    def __init__(self, commands: _SpyCommandsClient) -> None:
        self.commands = commands


class _CommandStubEnapterAPI(http.EnapterAPI):
    """Stub that injects a fake `commands` client for execute_command tests."""

    def __init__(self, base_url: str, commands: _SpyCommandsClient) -> None:
        super().__init__(base_url)
        self._commands = commands

    @contextlib.asynccontextmanager
    async def _new_client(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[enapter.http.api.Client, None]:
        yield cast(enapter.http.api.Client, _CommandFakeClient(self._commands))


# ---------------------------------------------------------------------------
#  Fixture helpers
# ---------------------------------------------------------------------------


def _make_execution(
    *,
    exec_id: str = "exec-1",
    device_id: str = "dev-1",
    state: enapter.http.api.commands.ExecutionState = (
        enapter.http.api.commands.ExecutionState.SUCCESS
    ),
    created_at: datetime.datetime | None = None,
    command_name: str = "cmd.power_on",
    arguments: dict[str, Any] | None = None,
    response_payload: dict[str, Any] | None = None,
    response_state: enapter.http.api.commands.response.ResponseState = (
        enapter.http.api.commands.response.ResponseState.SUCCEEDED
    ),
) -> enapter.http.api.commands.Execution:
    if created_at is None:
        created_at = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    if arguments is None:
        arguments = {}
    resp: enapter.http.api.commands.response.Response | None = None
    if response_payload is not None:
        resp = enapter.http.api.commands.response.Response(
            state=response_state,
            payload=response_payload,
            received_at=created_at,
        )
    return enapter.http.api.commands.Execution(
        id=exec_id,
        device_id=device_id,
        state=state,
        created_at=created_at,
        request=enapter.http.api.commands.request.Request(
            name=command_name, arguments=arguments
        ),
        response=resp,
        log=None,
    )


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------


class TestExecuteCommand:
    """Unit tests for http.EnapterAPI.execute_command."""

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _api(
        commands: _SpyCommandsClient,
    ) -> _CommandStubEnapterAPI:
        return _CommandStubEnapterAPI(base_url="http://example.test", commands=commands)

    @staticmethod
    def _auth() -> core.AuthConfig:
        return core.AuthConfig(token="test-token")

    # -- call-args ---------------------------------------------------------

    async def test_execute_passes_device_id_command_name_and_arguments(
        self,
    ) -> None:
        """commands.execute receives every positional argument unchanged."""
        spy = _SpyCommandsClient(
            result=_make_execution(
                device_id="dev-arg", command_name="cmd.foo", arguments={"a": 1}
            ),
        )
        api = self._api(spy)

        await api.execute_command(
            auth=self._auth(),
            device_id="dev-arg",
            command_name="cmd.foo",
            arguments={"a": 1},
        )

        assert spy.calls == [("dev-arg", "cmd.foo", {"a": 1})]

    async def test_execute_passes_none_arguments_unchanged(self) -> None:
        """None for `arguments` is passed through — the adapter does not pre-normalize."""
        spy = _SpyCommandsClient(
            result=_make_execution(arguments={}),
        )
        api = self._api(spy)

        await api.execute_command(
            auth=self._auth(),
            device_id="dev-1",
            command_name="cmd.foo",
            arguments=None,
        )

        assert spy.calls == [("dev-1", "cmd.foo", None)]

    # -- mapping on success -------------------------------------------------

    async def test_execute_maps_success_to_command_execution(self) -> None:
        """A successful SDK Execution maps to a domain.CommandExecution."""
        created = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        sdk_exec = _make_execution(
            exec_id="exec-mapped",
            device_id="dev-mapped",
            command_name="cmd.power_on",
            arguments={"power": 42},
            response_payload={"status": "on"},
            created_at=created,
        )
        spy = _SpyCommandsClient(result=sdk_exec)
        api = self._api(spy)

        result = await api.execute_command(
            auth=self._auth(),
            device_id="dev-mapped",
            command_name="cmd.power_on",
            arguments={"power": 42},
        )

        assert isinstance(result, domain.CommandExecution)
        assert result.id == "exec-mapped"
        assert result.device_id == "dev-mapped"
        assert result.command_name == "cmd.power_on"
        assert result.state == domain.CommandExecutionState.SUCCESS
        assert result.created_at == created
        assert result.arguments == {"power": 42}
        assert result.response_payload == {"status": "on"}

    async def test_execute_maps_null_response_to_none_payload(self) -> None:
        """When SDK response is None, response_payload is None."""
        sdk_exec = _make_execution(
            exec_id="exec-noresp",
            device_id="dev-noresp",
            command_name="cmd.foo",
            response_payload=None,
        )
        spy = _SpyCommandsClient(result=sdk_exec)
        api = self._api(spy)

        result = await api.execute_command(
            auth=self._auth(),
            device_id="dev-noresp",
            command_name="cmd.foo",
            arguments={},
        )

        assert result.response_payload is None
        assert result.id == "exec-noresp"

    # -- terminal states returned, not raised ------------------------------

    @pytest.mark.parametrize(
        "sdk_state,expected_state",
        [
            (
                enapter.http.api.commands.ExecutionState.ERROR,
                domain.CommandExecutionState.ERROR,
            ),
            (
                enapter.http.api.commands.ExecutionState.TIMEOUT,
                domain.CommandExecutionState.TIMEOUT,
            ),
            (
                enapter.http.api.commands.ExecutionState.UNSYNC,
                domain.CommandExecutionState.UNSYNC,
            ),
        ],
    )
    async def test_terminal_state_returned_not_raised(
        self,
        sdk_state: enapter.http.api.commands.ExecutionState,
        expected_state: domain.CommandExecutionState,
    ) -> None:
        """Terminal SDK states are mapped and returned — the adapter never raises."""
        sdk_exec = _make_execution(
            exec_id="exec-term",
            state=sdk_state,
            response_payload=None,
        )
        spy = _SpyCommandsClient(result=sdk_exec)
        api = self._api(spy)

        result = await api.execute_command(
            auth=self._auth(),
            device_id="dev-term",
            command_name="cmd.fail",
            arguments={},
        )

        assert isinstance(result, domain.CommandExecution)
        assert result.state == expected_state
        assert result.id == "exec-term"

    # -- SDK exceptions propagate uncaught ---------------------------------

    async def test_sdk_exception_propagates_unmodified(self) -> None:
        """When commands.execute raises, the exact exception propagates — no wrapping."""
        exc = enapter.http.api.Error(
            message="forbidden",
            code="missing_permission",
            details={"role": "viewer"},
        )
        spy = _SpyCommandsClient(raises=exc)
        api = self._api(spy)

        with pytest.raises(enapter.http.api.Error) as exc_info:
            await api.execute_command(
                auth=self._auth(),
                device_id="dev-1",
                command_name="cmd.foo",
                arguments=None,
            )

        assert exc_info.value is exc

    async def test_non_sdk_exception_propagates_unmodified(self) -> None:
        """An arbitrary exception from execute also propagates unmodified."""
        exc = ValueError("unexpected value")
        spy = _SpyCommandsClient(raises=exc)
        api = self._api(spy)

        with pytest.raises(ValueError) as exc_info:
            await api.execute_command(
                auth=self._auth(),
                device_id="dev-1",
                command_name="cmd.foo",
                arguments=None,
            )

        assert exc_info.value is exc

    # -- side_effect callback coverage ------------------------------------

    async def test_side_effect_receives_args_and_result_is_returned(
        self,
    ) -> None:
        """When a side_effect callable is configured, its args match and its
        return value flows through the adapter."""
        received: list[tuple[str, str, dict[str, Any] | None]] = []

        async def _side_effect(
            device_id: str,
            command_name: str,
            arguments: dict[str, Any] | None,
        ) -> enapter.http.api.commands.Execution:
            received.append((device_id, command_name, arguments))
            return _make_execution(
                exec_id="exec-side",
                device_id=device_id,
                command_name=command_name,
                arguments=arguments if arguments is not None else {},
            )

        spy = _SpyCommandsClient(side_effect=_side_effect)
        api = self._api(spy)

        result = await api.execute_command(
            auth=self._auth(),
            device_id="dev-side",
            command_name="cmd.test",
            arguments={"k": "v"},
        )

        assert received == [("dev-side", "cmd.test", {"k": "v"})]
        assert spy.calls == [("dev-side", "cmd.test", {"k": "v"})]
        assert result.id == "exec-side"
        assert result.arguments == {"k": "v"}


# ---------------------------------------------------------------------------
#  Fakes for rule-editing tests
# ---------------------------------------------------------------------------


class _SpyRuleEngineClient:
    """Records calls to create_rule/update_rule_script/delete_rule and returns
    pre-configured results, capturing the upstream RuleScript passed in."""

    def __init__(
        self,
        *,
        create_result: enapter.http.api.rule_engine.Rule | None = None,
        update_result: enapter.http.api.rule_engine.Rule | None = None,
        raises: Exception | None = None,
    ) -> None:
        self.create_result = create_result
        self.update_result = update_result
        self.raises = raises
        self.create_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []
        self.delete_calls: list[dict[str, Any]] = []

    async def create_rule(
        self,
        script: enapter.http.api.rule_engine.RuleScript,
        slug: str | None = None,
        site_id: str | None = None,
        disable: bool | None = None,
    ) -> enapter.http.api.rule_engine.Rule:
        self.create_calls.append(
            {"script": script, "slug": slug, "site_id": site_id, "disable": disable}
        )
        if self.raises is not None:
            raise self.raises
        if self.create_result is not None:
            return self.create_result
        raise NotImplementedError("No create_result configured")

    async def update_rule_script(
        self,
        rule_id: str,
        script: enapter.http.api.rule_engine.RuleScript,
        site_id: str | None = None,
    ) -> enapter.http.api.rule_engine.Rule:
        self.update_calls.append(
            {"rule_id": rule_id, "script": script, "site_id": site_id}
        )
        if self.raises is not None:
            raise self.raises
        if self.update_result is not None:
            return self.update_result
        raise NotImplementedError("No update_result configured")

    async def delete_rule(self, rule_id: str, site_id: str | None = None) -> None:
        self.delete_calls.append({"rule_id": rule_id, "site_id": site_id})
        if self.raises is not None:
            raise self.raises
        return None


class _RuleFakeClient:
    """Fake SDK Client exposing only `rule_engine`."""

    def __init__(self, rule_engine: _SpyRuleEngineClient) -> None:
        self.rule_engine = rule_engine


class _RuleStubEnapterAPI(http.EnapterAPI):
    """Stub that injects a spy `rule_engine` client for rule-editing tests."""

    def __init__(self, base_url: str, rule_engine: _SpyRuleEngineClient) -> None:
        super().__init__(base_url)
        self._rule_engine = rule_engine

    @contextlib.asynccontextmanager
    async def _new_client(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[enapter.http.api.Client, None]:
        yield cast(enapter.http.api.Client, _RuleFakeClient(self._rule_engine))


def _make_sdk_rule(
    *,
    rule_id: str = "rule-1",
    slug: str = "mcp-x",
    disabled: bool = True,
    state: enapter.http.api.rule_engine.RuleState = (
        enapter.http.api.rule_engine.RuleState.STOPPED
    ),
    code: str = "-- code\n",
    runtime_version: enapter.http.api.rule_engine.RuntimeVersion = (
        enapter.http.api.rule_engine.RuntimeVersion.V3
    ),
    exec_interval: str | None = None,
) -> enapter.http.api.rule_engine.Rule:
    return enapter.http.api.rule_engine.Rule(
        id=rule_id,
        slug=slug,
        disabled=disabled,
        state=state,
        script=enapter.http.api.rule_engine.RuleScript(
            code=code, runtime_version=runtime_version, exec_interval=exec_interval
        ),
    )


class TestRuleEditing:
    """Unit tests for http.EnapterAPI rule-editing methods."""

    @staticmethod
    def _api(rule_engine: _SpyRuleEngineClient) -> _RuleStubEnapterAPI:
        return _RuleStubEnapterAPI(
            base_url="http://example.test", rule_engine=rule_engine
        )

    @staticmethod
    def _auth() -> core.AuthConfig:
        return core.AuthConfig(token="test-token")

    async def test_update_rule_script_passes_exec_interval_through(self) -> None:
        """The current rule's exec_interval reaches the upstream RuleScript
        unchanged (regression guard: it was silently dropped)."""
        spy = _SpyRuleEngineClient(
            update_result=_make_sdk_rule(exec_interval="2m"),
        )
        api = self._api(spy)

        await api.update_rule_script(
            auth=self._auth(),
            rule_id="rule-1",
            site_id="site-1",
            script_code="new code",
            script_runtime_version=domain.RuleRuntimeVersion.V3,
            script_exec_interval="2m",
        )

        assert len(spy.update_calls) == 1
        script = spy.update_calls[0]["script"]
        assert script.exec_interval == "2m"
        assert script.code == "new code"
        assert script.runtime_version == (
            enapter.http.api.rule_engine.RuntimeVersion.V3
        )
        assert spy.update_calls[0]["rule_id"] == "rule-1"
        assert spy.update_calls[0]["site_id"] == "site-1"

    async def test_update_rule_script_passes_none_exec_interval(self) -> None:
        """exec_interval=None (the v3 case) is forwarded as None."""
        spy = _SpyRuleEngineClient(update_result=_make_sdk_rule())
        api = self._api(spy)

        await api.update_rule_script(
            auth=self._auth(),
            rule_id="rule-1",
            site_id="site-1",
            script_code="code",
            script_runtime_version=domain.RuleRuntimeVersion.V3,
            script_exec_interval=None,
        )

        assert spy.update_calls[0]["script"].exec_interval is None

    async def test_update_rule_script_uppercases_runtime_version(self) -> None:
        spy = _SpyRuleEngineClient(update_result=_make_sdk_rule())
        api = self._api(spy)

        await api.update_rule_script(
            auth=self._auth(),
            rule_id="rule-1",
            site_id="site-1",
            script_code="code",
            script_runtime_version=domain.RuleRuntimeVersion.V3,
            script_exec_interval=None,
        )

        assert spy.update_calls[0]["script"].runtime_version == (
            enapter.http.api.rule_engine.RuntimeVersion.V3
        )

    async def test_update_rule_script_maps_result_to_rule_dto(self) -> None:
        spy = _SpyRuleEngineClient(
            update_result=_make_sdk_rule(
                rule_id="r", slug="mcp-s", disabled=True, exec_interval=None
            ),
        )
        api = self._api(spy)

        result = await api.update_rule_script(
            auth=self._auth(),
            rule_id="r",
            site_id="s",
            script_code="c",
            script_runtime_version=domain.RuleRuntimeVersion.V3,
            script_exec_interval=None,
        )

        assert isinstance(result, core.RuleDTO)
        assert result.id == "r"
        assert result.slug == "mcp-s"
        assert result.disabled is True
        assert result.script_runtime_version == domain.RuleRuntimeVersion.V3
        assert result.script_exec_interval is None

    async def test_create_rule_builds_v3_script_and_disables(self) -> None:
        spy = _SpyRuleEngineClient(create_result=_make_sdk_rule())
        api = self._api(spy)

        await api.create_rule(
            auth=self._auth(),
            site_id="site-1",
            slug="mcp-x",
            script_code="code",
            script_runtime_version=domain.RuleRuntimeVersion.V3,
            disabled=True,
        )

        assert len(spy.create_calls) == 1
        call = spy.create_calls[0]
        assert call["slug"] == "mcp-x"
        assert call["site_id"] == "site-1"
        assert call["disable"] is True
        script = call["script"]
        assert script.code == "code"
        assert script.runtime_version == (
            enapter.http.api.rule_engine.RuntimeVersion.V3
        )
        assert script.exec_interval is None

    async def test_delete_rule_calls_upstream_with_ids(self) -> None:
        spy = _SpyRuleEngineClient()
        api = self._api(spy)

        await api.delete_rule(auth=self._auth(), rule_id="rule-1", site_id="site-1")

        assert spy.delete_calls == [
            {"rule_id": "rule-1", "site_id": "site-1"},
        ]

    async def test_rule_sdk_exception_propagates_unmodified(self) -> None:
        exc = enapter.http.api.Error(
            message="forbidden", code="missing_permission", details={}
        )
        spy = _SpyRuleEngineClient(update_result=_make_sdk_rule(), raises=exc)
        api = self._api(spy)

        with pytest.raises(enapter.http.api.Error) as exc_info:
            await api.update_rule_script(
                auth=self._auth(),
                rule_id="rule-1",
                site_id="site-1",
                script_code="c",
                script_runtime_version=domain.RuleRuntimeVersion.V3,
                script_exec_interval=None,
            )

        assert exc_info.value is exc
