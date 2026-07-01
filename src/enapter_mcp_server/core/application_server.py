import asyncio
import datetime
import re
from typing import Any

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .command_execution_search_query import CommandExecutionSearchQuery
from .device_search_query import DeviceSearchQuery
from .enapter_api import EnapterAPI
from .errors import (
    CommandNotFound,
    ConfirmationRequired,
    GatewayUnavailable,
    SearchQueryTooBroad,
)
from .rule_search_query import RuleSearchQuery
from .site_search_query import SiteSearchQuery


class ApplicationServer:

    def __init__(self, enapter_api: EnapterAPI) -> None:
        self._enapter_api = enapter_api

    async def search_sites(
        self,
        auth: AuthConfig,
        query: SiteSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.Site]:
        sites = await self._search_sites(auth, query)
        sites.sort(key=lambda s: s.id)
        return sites[offset : offset + limit]

    async def _search_sites(
        self, auth: AuthConfig, query: SiteSearchQuery
    ) -> list[domain.Site]:
        semaphore = asyncio.Semaphore(10)

        async def enrich(site: domain.Site) -> domain.Site:
            async with semaphore:
                status = await self._compute_site_status(auth, site.id)
                return site.with_status(status)

        tasks = []
        async with asyncio.TaskGroup() as tg:
            async with self._enapter_api.list_sites(auth) as sites_gen:
                async for site in sites_gen:
                    if not query.matches(site):
                        continue

                    tasks.append(tg.create_task(enrich(site)))

        return [task.result() for task in tasks]

    async def _compute_site_status(
        self, auth: AuthConfig, site_id: str
    ) -> domain.SiteStatus:
        gateway_id: str | None = None
        gateway_online = False
        devices_online = 0
        device_ids: list[str] = []

        async with self._enapter_api.list_devices(
            auth, site_id=site_id, expand_connectivity=True
        ) as devices_gen:
            async for device in devices_gen:
                device_ids.append(device.id)
                if device.is_online:
                    devices_online += 1

                if device.is_gateway:
                    gateway_id = device.id
                    gateway_online = device.is_online is True

        rule_engine_state: domain.RuleEngineState | None = None
        if gateway_online:
            engine = await self._enapter_api.get_rule_engine(auth, site_id)
            rule_engine_state = engine.state

        return domain.SiteStatus(
            gateway_id=gateway_id,
            gateway_online=gateway_online,
            devices_total=len(device_ids),
            devices_online=devices_online,
            rule_engine_state=rule_engine_state,
        )

    async def search_rules(
        self,
        auth: AuthConfig,
        query: RuleSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.Rule]:
        await self._assert_gateway_online(auth, query.site_id)
        rules = await self._search_rules(auth, query)
        rules.sort(key=lambda r: r.id)
        return rules[offset : offset + limit]

    async def _search_rules(
        self, auth: AuthConfig, query: RuleSearchQuery
    ) -> list[domain.Rule]:
        rules: list[domain.Rule] = []
        async with self._enapter_api.list_rules(auth, query.site_id) as rules_gen:
            async for rule in rules_gen:
                if not query.matches(rule):
                    continue

                rules.append(rule)

        return rules

    async def read_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        rule_id: str,
        offset: int,
        limit: int,
    ) -> list[str]:
        await self._assert_gateway_online(auth, site_id)
        rule = await self._enapter_api.get_rule(auth, site_id, rule_id)
        lines = rule.script.code.splitlines()
        return lines[offset : offset + limit]

    async def create_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        slug: str,
        script_code: str,
    ) -> domain.Rule:
        await self._assert_gateway_online(auth, site_id)
        if not slug.startswith(domain.MCP_PREFIX):
            raise domain.UnprefixedRuleSlug(
                f"The slug {slug!r} does not start with the MCP-managed"
                f" prefix {domain.MCP_PREFIX!r}."
            )
        return await self._enapter_api.create_rule(
            auth,
            site_id,
            slug,
            domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code=script_code,
            ),
            disabled=True,
        )

    async def edit_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        rule_id: str,
        old_string: str,
        new_string: str,
    ) -> domain.Rule:
        await self._assert_gateway_online(auth, site_id)

        if old_string == "":
            raise domain.EmptyRuleOldString(
                "An empty old_string is not allowed. Provide the exact"
                " snippet of the current script you wish to replace."
            )
        if old_string == new_string:
            raise domain.NoOpRuleEdit(
                "The old_string and new_string are identical. This"
                " would not change the rule's script."
            )

        rule = await self._enapter_api.get_rule(auth, site_id, rule_id)

        if not rule.disabled:
            raise domain.RuleNotDisabled(
                f"Rule {rule_id!r} is enabled. Please disable it in"
                f" the Enapter UI before editing it via MCP."
            )
        if not rule.is_mcp_managed:
            raise domain.RuleNotMcpManaged(
                f"Rule {rule_id!r} has slug {rule.slug!r}, which"
                f" does not start with the MCP-managed prefix"
                f" {domain.MCP_PREFIX!r}."
            )
        if rule.script.runtime_version != domain.RuleRuntimeVersion.V3:
            raise domain.RuleNotV3(
                f"Rule {rule_id!r} uses runtime version"
                f" {rule.script.runtime_version.value!r}, but"
                f" edit_rule only supports v3 rules."
            )

        code = rule.script.code
        count = code.count(old_string)
        if count == 0:
            raise domain.RuleOldStringNotFound(
                f"The old_string was not found anywhere in the"
                f" current script of rule {rule_id!r}. The script may"
                f" have been changed; use read_rule to get the latest"
                f" content."
            )
        if count > 1:
            raise domain.AmbiguousRuleOldString(
                f"The old_string appears {count} times in the"
                f" current script of rule {rule_id!r}. Include more"
                f" surrounding context to make the match unique."
            )

        new_code = code.replace(old_string, new_string, 1)

        # The upstream API has no conditional-update primitive (no ETags).
        # Between the preceding get_rule fetch and this update_rule_script
        # call a concurrent change (enable, rename) is possible. This race
        # window is accepted in v1. When the platform adds ETags the gap
        # can be closed deliberately.
        return await self._enapter_api.update_rule_script(
            auth,
            rule_id,
            site_id,
            domain.RuleScript(
                runtime_version=rule.script.runtime_version,
                exec_interval=rule.script.exec_interval,
                code=new_code,
            ),
        )

    async def delete_rule(
        self,
        auth: AuthConfig,
        site_id: str,
        rule_id: str,
    ) -> None:
        await self._assert_gateway_online(auth, site_id)
        rule = await self._enapter_api.get_rule(auth, site_id, rule_id)

        if not rule.disabled:
            raise domain.RuleNotDisabled(
                f"Rule {rule_id!r} is enabled. Please disable it in"
                f" the Enapter UI before deleting it via MCP."
            )
        if not rule.is_mcp_managed:
            raise domain.RuleNotMcpManaged(
                f"Rule {rule_id!r} has slug {rule.slug!r}, which"
                f" does not start with the MCP-managed prefix"
                f" {domain.MCP_PREFIX!r}."
            )

        # The upstream API has no conditional-update primitive (no ETags).
        # Between the preceding get_rule fetch and this delete call a
        # concurrent change (enable, rename) is possible. This race window
        # is accepted in v1.
        await self._enapter_api.delete_rule(auth, rule_id, site_id)

    async def _assert_gateway_online(self, auth: AuthConfig, site_id: str) -> None:
        async with self._enapter_api.list_devices(
            auth,
            site_id=site_id,
            expand_connectivity=True,
        ) as devices_gen:
            async for device in devices_gen:
                if not device.is_gateway:
                    continue
                if device.is_online:
                    return
                raise GatewayUnavailable("The site's gateway is currently offline.")

        raise GatewayUnavailable("The site has no gateway.")

    async def search_devices(
        self,
        auth: AuthConfig,
        query: DeviceSearchQuery,
        offset: int,
        limit: int,
        view: domain.DeviceViewType,
    ) -> list[domain.DeviceView]:
        match view:
            case domain.DeviceViewType.BASIC:
                views = await self._search_devices_basic(auth, query)
            case domain.DeviceViewType.FULL:
                views = await self._search_devices_full(auth, query)
            case _:
                raise NotImplementedError(view)

        views.sort(key=lambda v: v.id)
        return views[offset : offset + limit]

    async def _search_devices_basic(
        self, auth: AuthConfig, query: DeviceSearchQuery
    ) -> list[domain.DeviceView]:
        views: list[domain.DeviceView] = []
        async with self._enapter_api.list_devices(
            auth,
            site_id=query.site_id,
            expand_manifest=True,
            expand_connectivity=True,
            expand_active_alerts=True,
        ) as devices_gen:
            async for device in devices_gen:
                if query.matches(device):
                    views.append(domain.DeviceViewBasic(device))

        return views

    async def _search_devices_full(
        self, auth: AuthConfig, query: DeviceSearchQuery
    ) -> list[domain.DeviceView]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `site_id` or `device_id` to narrow down the search."
            )

        views: list[domain.DeviceView] = []
        async with self._enapter_api.list_devices(
            auth,
            site_id=query.site_id,
            expand_manifest=True,
            expand_properties=True,
            expand_connectivity=True,
            expand_active_alerts=True,
        ) as devices_gen:
            async for device in devices_gen:
                if query.matches(device):
                    views.append(domain.DeviceViewFull(device))

        return views

    async def read_blueprint(
        self,
        auth: AuthConfig,
        device_id: str,
        section: domain.BlueprintSection,
        name_regexp: str,
        offset: int,
        limit: int,
    ) -> list[
        str
        | domain.PropertyDeclaration
        | domain.TelemetryAttributeDeclaration
        | domain.AlertDeclaration
        | domain.CommandDeclaration
    ]:
        name_pattern = re.compile(name_regexp)
        device = await self._enapter_api.get_device(
            auth, device_id, expand_manifest=True
        )
        assert device.manifest is not None

        entities: list[
            str
            | domain.PropertyDeclaration
            | domain.TelemetryAttributeDeclaration
            | domain.AlertDeclaration
            | domain.CommandDeclaration
        ] = []

        match section:
            case domain.BlueprintSection.IMPLEMENTS:
                entities = list(device.manifest.implements)
            case domain.BlueprintSection.PROPERTIES:
                entities = list(device.manifest.properties.values())
            case domain.BlueprintSection.TELEMETRY:
                entities = list(device.manifest.telemetry.values())
            case domain.BlueprintSection.ALERTS:
                entities = list(device.manifest.alerts.values())
            case domain.BlueprintSection.COMMANDS:
                entities = list(device.manifest.commands.values())
            case _:
                raise NotImplementedError(section)

        key = lambda e: e if isinstance(e, str) else e.name
        entities = [e for e in entities if name_pattern.search(key(e))]
        entities.sort(key=key)
        return entities[offset : offset + limit]

    async def execute_command(
        self,
        auth: AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None = None,
        human_confirmed_this_action: bool = False,
    ) -> domain.CommandExecution:
        commands = await self._resolve_manifest_commands(auth, device_id)
        declaration = commands.get(command_name)
        if declaration is None:
            available = ", ".join(sorted(commands)) or "(none)"
            raise CommandNotFound(
                f"Command {command_name!r} is not declared in the manifest of"
                f" device {device_id!r}. Available commands: {available}."
            )
        if declaration.confirmation is not None and not human_confirmed_this_action:
            confirmation = declaration.confirmation
            title = confirmation.title or declaration.display_name
            description = confirmation.description
            raise ConfirmationRequired(
                f"Command {command_name!r} on device {device_id!r} requires human"
                f" confirmation before execution. Title: {title}."
                f" Description: {description}."
            )
        return await self._enapter_api.execute_command(
            auth, device_id, command_name, arguments
        )

    async def _resolve_manifest_commands(
        self, auth: AuthConfig, device_id: str
    ) -> dict[str, domain.CommandDeclaration]:
        device = await self._enapter_api.get_device(
            auth, device_id, expand_manifest=True
        )
        assert device.manifest is not None
        return device.manifest.commands

    async def get_historical_telemetry(
        self,
        auth: AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
        aggregation: domain.AggregationFunction,
    ) -> domain.HistoricalTelemetry:
        return await self._enapter_api.get_historical_telemetry(
            auth,
            device_id,
            attributes,
            time_from,
            time_to,
            granularity,
            aggregation,
        )

    async def search_command_executions(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
        view: domain.CommandExecutionView,
    ) -> list[domain.CommandExecution]:
        match view:
            case domain.CommandExecutionView.BASIC:
                return await self._search_command_executions_basic(
                    auth, query, offset, limit
                )
            case domain.CommandExecutionView.FULL:
                return await self._search_command_executions_full(
                    auth, query, offset, limit
                )
            case _:
                raise NotImplementedError(view)

    async def _search_command_executions_basic(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.CommandExecution]:
        if query.site_id is None and query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `site_id` or `device_id` to narrow down the search."
            )

        executions: list[domain.CommandExecution] = []
        skipped = 0

        async with self._enapter_api.list_command_executions(
            auth,
            device_id=query.device_id,
            site_id=query.site_id,
            created_at_gte=query.created_at_gte,
            created_at_lt=query.created_at_lt,
            state=query.state,
        ) as executions_gen:
            async for execution in executions_gen:
                if query.matches(execution):
                    if skipped < offset:
                        skipped += 1
                        continue

                    executions.append(execution.strip())
                    if len(executions) >= limit:
                        break

        return executions

    async def _search_command_executions_full(
        self,
        auth: AuthConfig,
        query: CommandExecutionSearchQuery,
        offset: int,
        limit: int,
    ) -> list[domain.CommandExecution]:
        if query.device_id is None:
            raise SearchQueryTooBroad(
                "Please provide `device_id` to narrow down the search."
            )

        executions: list[domain.CommandExecution] = []
        skipped = 0

        async with self._enapter_api.list_command_executions(
            auth,
            device_id=query.device_id,
            site_id=query.site_id,
            created_at_gte=query.created_at_gte,
            created_at_lt=query.created_at_lt,
            state=query.state,
        ) as executions_gen:
            async for execution in executions_gen:
                if query.matches(execution):
                    if skipped < offset:
                        skipped += 1
                        continue

                    executions.append(execution)
                    if len(executions) >= limit:
                        break

        return executions
