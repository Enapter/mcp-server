import datetime
from typing import Any, AsyncGenerator, Protocol

from enapter_mcp_server import core, domain

from .state import State


class Policy(Protocol):
    async def list_sites(
        self, state: State, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
        yield  # type: ignore

    async def get_rule_engine(
        self, state: State, auth: core.AuthConfig, site_id: str
    ) -> domain.RuleEngine: ...

    async def list_rules(
        self, state: State, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[domain.Rule, None]:
        yield  # type: ignore

    async def get_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str,
        rule_id: str,
    ) -> domain.Rule: ...

    async def list_devices(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
        expand_active_alerts: bool = False,
    ) -> AsyncGenerator[domain.Device, None]:
        yield  # type: ignore

    async def get_device(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device: ...

    async def execute_command(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution: ...

    async def list_command_executions(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str | None = None,
        site_id: str | None = None,
        created_at_gte: datetime.datetime | None = None,
        created_at_lt: datetime.datetime | None = None,
        execution_state: domain.CommandExecutionState | None = None,
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        yield  # type: ignore

    async def get_latest_telemetry(
        self,
        state: State,
        auth: core.AuthConfig,
        attributes_by_device: dict[str, list[str]],
    ) -> dict[str, dict[str, Any]]: ...

    async def get_historical_telemetry(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry: ...

    async def create_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule: ...

    async def update_rule_script(
        self,
        state: State,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
        script: domain.RuleScript,
    ) -> domain.Rule: ...

    async def delete_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
    ) -> None: ...


class DefaultPolicy:
    async def list_sites(
        self, state: State, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
        for site in state.sites:
            yield site

    async def get_rule_engine(
        self, state: State, auth: core.AuthConfig, site_id: str
    ) -> domain.RuleEngine:
        for engine in state.rule_engines:
            if engine.id == site_id:
                return engine
        raise core.RuleEngineNotFound(site_id=site_id)

    async def list_rules(
        self, state: State, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[domain.Rule, None]:
        for rule in state.rules:
            yield rule

    async def get_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str,
        rule_id: str,
    ) -> domain.Rule:
        for rule in state.rules:
            if rule.id == rule_id or rule.slug == rule_id:
                return rule
        raise core.RuleNotFound(rule_id=rule_id, site_id=site_id)

    async def list_devices(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
        expand_active_alerts: bool = False,
    ) -> AsyncGenerator[domain.Device, None]:
        for device in state.devices:
            if site_id is not None and device.site_id != site_id:
                continue
            yield device

    async def get_device(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device:
        for device in state.devices:
            if device.id == device_id:
                return device
        raise core.DeviceNotFound(device_id=device_id)

    async def execute_command(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution:
        raise NotImplementedError

    async def list_command_executions(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str | None = None,
        site_id: str | None = None,
        created_at_gte: datetime.datetime | None = None,
        created_at_lt: datetime.datetime | None = None,
        execution_state: domain.CommandExecutionState | None = None,
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        matches: list[domain.CommandExecution] = []
        for execution in state.command_executions:
            if device_id is not None and execution.device_id != device_id:
                continue
            if site_id is not None:
                device = next(
                    (d for d in state.devices if d.id == execution.device_id), None
                )
                if device is None or device.site_id != site_id:
                    continue
            if created_at_gte is not None and execution.created_at < created_at_gte:
                continue
            if created_at_lt is not None and execution.created_at >= created_at_lt:
                continue
            if execution_state is not None and execution.state != execution_state:
                continue
            matches.append(execution)

        matches.sort(key=lambda e: e.created_at, reverse=True)
        for execution in matches:
            yield execution

    async def get_latest_telemetry(
        self,
        state: State,
        auth: core.AuthConfig,
        attributes_by_device: dict[str, list[str]],
    ) -> dict[str, dict[str, Any]]:
        return {}

    async def get_historical_telemetry(
        self,
        state: State,
        auth: core.AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry:
        return domain.HistoricalTelemetry(timestamps=[], values={})

    async def create_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule:
        raise NotImplementedError

    async def update_rule_script(
        self,
        state: State,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
        script: domain.RuleScript,
    ) -> domain.Rule:
        raise NotImplementedError

    async def delete_rule(
        self,
        state: State,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
    ) -> None:
        raise NotImplementedError
