import datetime
import importlib
import urllib.parse
from typing import Any, AsyncGenerator, Self

import enapter

from enapter_mcp_server import core, domain

from .policy import DefaultPolicy, Policy
from .state import State


class EnapterAPI:
    def __init__(self, state: State, policy: Policy) -> None:
        self.state = state
        self.policy = policy

    @classmethod
    def from_url(cls, url: str) -> Self:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        state = importlib.import_module(q["state"][0]).state()
        if "policy" in q:
            policy: Policy = getattr(
                importlib.import_module(q["policy"][0]), "Policy"
            )()
        else:
            policy = DefaultPolicy()
        return cls(state=state, policy=policy)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    @enapter.async_.generator
    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
        async for site in self.policy.list_sites(self.state, auth):
            yield site

    async def get_rule_engine(
        self, auth: core.AuthConfig, site_id: str
    ) -> domain.RuleEngine:
        return await self.policy.get_rule_engine(self.state, auth, site_id)

    @enapter.async_.generator
    async def list_rules(
        self, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[domain.Rule, None]:
        async for rule in self.policy.list_rules(self.state, auth, site_id):
            yield rule

    async def get_rule(
        self, auth: core.AuthConfig, site_id: str, rule_id: str
    ) -> domain.Rule:
        return await self.policy.get_rule(self.state, auth, site_id, rule_id)

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
        async for device in self.policy.list_devices(
            self.state,
            auth,
            site_id=site_id,
            expand_manifest=expand_manifest,
            expand_properties=expand_properties,
            expand_connectivity=expand_connectivity,
            expand_active_alerts=expand_active_alerts,
        ):
            yield device

    async def get_device(
        self,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device:
        return await self.policy.get_device(
            self.state,
            auth,
            device_id,
            expand_manifest=expand_manifest,
            expand_connectivity=expand_connectivity,
            expand_properties=expand_properties,
            expand_active_alerts=expand_active_alerts,
        )

    async def execute_command(
        self,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution:
        return await self.policy.execute_command(
            self.state, auth, device_id, command_name, arguments
        )

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
        async for execution in self.policy.list_command_executions(
            self.state,
            auth,
            device_id,
            site_id,
            created_at_gte,
            created_at_lt,
            state,
        ):
            yield execution

    async def get_latest_telemetry(
        self, auth: core.AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]:
        return await self.policy.get_latest_telemetry(
            self.state, auth, attributes_by_device
        )

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
        return await self.policy.get_historical_telemetry(
            self.state,
            auth,
            device_id,
            attributes,
            time_from,
            time_to,
            granularity,
            aggregation,
        )

    async def create_rule(
        self,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule:
        return await self.policy.create_rule(
            self.state, auth, site_id, slug, script, disabled
        )

    async def update_rule_script(
        self,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
        script: domain.RuleScript,
    ) -> domain.Rule:
        return await self.policy.update_rule_script(
            self.state, auth, rule_id, site_id, script
        )

    async def delete_rule(
        self, auth: core.AuthConfig, rule_id: str, site_id: str
    ) -> None:
        await self.policy.delete_rule(self.state, auth, rule_id, site_id)
