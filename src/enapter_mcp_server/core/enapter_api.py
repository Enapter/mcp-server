import datetime
from typing import Any, AsyncGenerator, Protocol

import enapter

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .device_dto import DeviceDTO
from .site_dto import SiteDTO


class EnapterAPI(Protocol):
    @enapter.async_.generator
    async def list_sites(self, auth: AuthConfig) -> AsyncGenerator[SiteDTO, None]:
        yield  # type: ignore

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: AuthConfig,
        site_id: str | None = None,
        expand_manifest: bool = False,
        expand_properties: bool = False,
        expand_connectivity: bool = False,
    ) -> AsyncGenerator[DeviceDTO, None]:
        yield  # type: ignore

    async def get_device(
        self,
        auth: AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
    ) -> DeviceDTO: ...

    @enapter.async_.generator
    async def list_command_executions(
        self, auth: AuthConfig, device_id: str
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
        aggregation: enapter.http.api.telemetry.Aggregation,
    ) -> domain.HistoricalTelemetry: ...
