import datetime
from typing import Any, AsyncGenerator, Protocol

import enapter

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .rule_dto import RuleDTO
from .rule_engine_dto import RuleEngineDTO
from .site_dto import SiteDTO


class EnapterAPI(Protocol):
    @enapter.async_.generator
    async def list_sites(self, auth: AuthConfig) -> AsyncGenerator[SiteDTO, None]:
        yield  # type: ignore

    async def get_rule_engine(
        self, auth: AuthConfig, site_id: str
    ) -> RuleEngineDTO: ...

    @enapter.async_.generator
    async def list_rules(
        self, auth: AuthConfig, site_id: str
    ) -> AsyncGenerator[RuleDTO, None]:
        yield  # type: ignore

    async def get_rule(
        self, auth: AuthConfig, site_id: str, rule_id: str
    ) -> RuleDTO: ...

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
        expand_active_alerts: bool = False,
    ) -> AsyncGenerator[domain.Device, None]:
        yield  # type: ignore

    async def get_device(
        self,
        auth: AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device: ...

    async def execute_command(
        self,
        auth: AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution: ...

    @enapter.async_.generator
    async def list_command_executions(
        self,
        auth: AuthConfig,
        device_id: str | None = None,
        site_id: str | None = None,
        created_at_gte: datetime.datetime | None = None,
        created_at_lt: datetime.datetime | None = None,
        state: domain.CommandExecutionState | None = None,
    ) -> AsyncGenerator[domain.CommandExecution, None]:
        yield  # type: ignore

    async def get_latest_telemetry(
        self, auth: AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]: ...

    async def get_historical_telemetry(
        self,
        auth: AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry: ...

    async def create_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        slug: str,
        script_code: str,
        script_runtime_version: domain.RuleRuntimeVersion,
        disabled: bool,
    ) -> RuleDTO: ...

    async def update_rule_script(
        self,
        auth: AuthConfig,
        rule_id: str,
        site_id: str,
        script_code: str,
        script_runtime_version: domain.RuleRuntimeVersion,
        script_exec_interval: str | None,
    ) -> RuleDTO: ...

    async def delete_rule(
        self, auth: AuthConfig, rule_id: str, site_id: str
    ) -> None: ...
