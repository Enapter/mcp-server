import datetime
from typing import Any, AsyncGenerator, Protocol

from enapter_mcp_server import domain

from .auth_config import AuthConfig


class EnapterAPI(Protocol):

    async def list_sites(self, auth: AuthConfig) -> AsyncGenerator[domain.Site, None]:
        yield  # type: ignore

    async def get_site(self, auth: AuthConfig, site_id: str) -> domain.Site: ...

    async def list_devices(
        self,
        auth: AuthConfig,
        site_id: str | None = None,
        expand_connectivity: bool = False,
    ) -> AsyncGenerator[domain.Device, None]:
        yield  # type: ignore

    async def get_device(
        self,
        auth: AuthConfig,
        device_id: str,
        expand_manifest: bool = False,
        expand_connectivity: bool = False,
        expand_properties: bool = False,
    ) -> domain.Device: ...

    async def get_latest_telemetry(
        self, auth: AuthConfig, device_id: str, attributes: list[str]
    ) -> dict[str, Any]: ...

    async def get_historical_telemetry(
        self,
        auth: AuthConfig,
        device_id: str,
        attributes: list[str],
        time_from: datetime.datetime,
        time_to: datetime.datetime,
        granularity: int,
    ) -> domain.HistoricalTelemetry: ...
