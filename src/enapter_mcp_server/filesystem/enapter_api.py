import dataclasses
import datetime
import os
import pathlib
import re
import tempfile
import uuid
from typing import Any, AsyncGenerator, Self

import enapter
import yaml

from enapter_mcp_server import core, domain

from . import models

_ID_RE = re.compile(r"^[a-z0-9]([a-z0-9]-?)*[a-z0-9]$")


class EnapterAPI:

    def __init__(self, state_dir: pathlib.Path) -> None:
        self._state_dir = state_dir

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    def _validate_id(self, value: str) -> None:
        if not _ID_RE.match(value):
            raise ValueError(f"Invalid ID: {value!r}")

    def _atomic_write(self, path: pathlib.Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.replace(tmp_path, path)
        except BaseException:
            os.unlink(tmp_path)
            raise

    @enapter.async_.generator
    async def list_sites(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[domain.Site, None]:
        sites_dir = self._state_dir / "sites"
        if not sites_dir.exists():
            return
        for path in sorted(sites_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text())
            model = models.SiteAggregate.model_validate(data)
            yield model.site.to_domain()

    async def get_rule_engine(
        self, auth: core.AuthConfig, site_id: str
    ) -> domain.RuleEngine:
        self._validate_id(site_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            raise core.RuleEngineNotFound(site_id=site_id)
        data = yaml.safe_load(path.read_text())
        model = models.RuleEngineAggregate.model_validate(data)
        return model.rule_engine.to_domain()

    @enapter.async_.generator
    async def list_rules(
        self, auth: core.AuthConfig, site_id: str
    ) -> AsyncGenerator[domain.Rule, None]:
        self._validate_id(site_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            return
        data = yaml.safe_load(path.read_text())
        model = models.RuleEngineAggregate.model_validate(data)
        for rule_model in model.rules:
            yield rule_model.to_domain()

    async def get_rule(
        self, auth: core.AuthConfig, site_id: str, rule_id: str
    ) -> domain.Rule:
        self._validate_id(site_id)
        self._validate_id(rule_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            raise core.RuleEngineNotFound(site_id=site_id)
        data = yaml.safe_load(path.read_text())
        model = models.RuleEngineAggregate.model_validate(data)
        for rule_model in model.rules:
            if rule_model.id == rule_id or rule_model.slug == rule_id:
                return rule_model.to_domain()
        raise core.RuleNotFound(rule_id=rule_id, site_id=site_id)

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
        if site_id is not None:
            self._validate_id(site_id)
            path = self._state_dir / "sites" / f"{site_id}.yaml"
            if not path.exists():
                return
            data = yaml.safe_load(path.read_text())
            model = models.SiteAggregate.model_validate(data)
            for device_model in model.devices:
                yield device_model.to_domain()
        else:
            sites_dir = self._state_dir / "sites"
            if not sites_dir.exists():
                return
            for path in sorted(sites_dir.glob("*.yaml")):
                data = yaml.safe_load(path.read_text())
                model = models.SiteAggregate.model_validate(data)
                for device_model in model.devices:
                    yield device_model.to_domain()

    async def get_device(
        self,
        auth: core.AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
        expand_active_alerts: bool = False,
    ) -> domain.Device:
        self._validate_id(device_id)
        sites_dir = self._state_dir / "sites"
        if sites_dir.exists():
            for path in sorted(sites_dir.glob("*.yaml")):
                data = yaml.safe_load(path.read_text())
                model = models.SiteAggregate.model_validate(data)
                for device_model in model.devices:
                    if (
                        device_model.id == device_id
                        or getattr(device_model, "slug", None) == device_id
                    ):
                        return device_model.to_domain()
        raise core.DeviceNotFound(device_id=device_id)

    async def execute_command(
        self,
        auth: core.AuthConfig,
        device_id: str,
        command_name: str,
        arguments: dict[str, Any] | None,
    ) -> domain.CommandExecution:
        self._validate_id(device_id)
        raise NotImplementedError

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
        raise NotImplementedError
        yield  # type: ignore

    async def get_latest_telemetry(
        self, auth: core.AuthConfig, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, Any]]:
        raise NotImplementedError

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
        self._validate_id(device_id)
        raise NotImplementedError

    async def create_rule(
        self,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule:
        self._validate_id(site_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            raise core.RuleEngineNotFound(site_id=site_id)
        data = yaml.safe_load(path.read_text())
        file_model = models.RuleEngineAggregate.model_validate(data)
        for rule_model in file_model.rules:
            if rule_model.slug == slug:
                raise core.RuleSlugConflict(slug=slug, site_id=site_id)
        rule = domain.Rule(
            id=uuid.uuid4().hex,
            slug=slug,
            disabled=disabled,
            state=(
                domain.RuleState.STARTED if not disabled else domain.RuleState.STOPPED
            ),
            script=script,
        )
        file_model.rules.append(models.Rule.from_domain(rule))
        file_data = file_model.model_dump(mode="json", exclude_none=True)
        content = yaml.dump(
            file_data, sort_keys=False, allow_unicode=True, default_flow_style=False
        )
        self._atomic_write(path, content)
        return rule

    async def update_rule_script(
        self,
        auth: core.AuthConfig,
        rule_id: str,
        site_id: str,
        script: domain.RuleScript,
    ) -> domain.Rule:
        self._validate_id(rule_id)
        self._validate_id(site_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            raise core.RuleEngineNotFound(site_id=site_id)
        data = yaml.safe_load(path.read_text())
        file_model = models.RuleEngineAggregate.model_validate(data)
        for i, rule_model in enumerate(file_model.rules):
            if rule_model.id == rule_id or rule_model.slug == rule_id:
                rule = rule_model.to_domain()
                updated_rule = dataclasses.replace(rule, script=script)
                file_model.rules[i] = models.Rule.from_domain(updated_rule)
                file_data = file_model.model_dump(mode="json", exclude_none=True)
                content = yaml.dump(
                    file_data,
                    sort_keys=False,
                    allow_unicode=True,
                    default_flow_style=False,
                )
                self._atomic_write(path, content)
                return updated_rule
        raise core.RuleNotFound(rule_id=rule_id, site_id=site_id)

    async def delete_rule(
        self, auth: core.AuthConfig, rule_id: str, site_id: str
    ) -> None:
        self._validate_id(rule_id)
        self._validate_id(site_id)
        path = self._state_dir / "rule_engines" / f"{site_id}.yaml"
        if not path.exists():
            raise core.RuleEngineNotFound(site_id=site_id)
        data = yaml.safe_load(path.read_text())
        file_model = models.RuleEngineAggregate.model_validate(data)
        for i, rule_model in enumerate(file_model.rules):
            if rule_model.id == rule_id or rule_model.slug == rule_id:
                file_model.rules.pop(i)
                file_data = file_model.model_dump(mode="json", exclude_none=True)
                content = yaml.dump(
                    file_data,
                    sort_keys=False,
                    allow_unicode=True,
                    default_flow_style=False,
                )
                self._atomic_write(path, content)
                return
        raise core.RuleNotFound(rule_id=rule_id, site_id=site_id)
