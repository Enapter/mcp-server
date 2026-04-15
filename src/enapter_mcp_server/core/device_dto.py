import dataclasses
from typing import Any

from enapter_mcp_server import domain


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceDTO:
    id: str
    name: str
    site_id: str
    type: domain.DeviceType
    connectivity: domain.ConnectivityStatus | None = None
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None
    manifest: domain.DeviceManifest | None = None
