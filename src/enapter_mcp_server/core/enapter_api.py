import datetime
from typing import AsyncGenerator, Protocol

import enapter

from enapter_mcp_server import domain

from .auth_config import AuthConfig
from .device_dto import DeviceDTO


class EnapterAPI(Protocol):

    @enapter.async_.generator
    async def list_sites(self, auth: AuthConfig) -> AsyncGenerator[domain.Site, None]:
        yield  # type: ignore

    async def get_site(self, auth: AuthConfig, site_id: str) -> domain.Site: ...

    @enapter.async_.generator
    async def list_devices(
        self,
        auth: AuthConfig,
        site_id: str | None = None,
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

    async def get_historical_telemetry(
        self,
        auth: AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
    ) -> domain.HistoricalTelemetry: ...
