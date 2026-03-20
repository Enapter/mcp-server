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
    manifest: dict[str, Any] | None = None

    def to_domain(self) -> domain.Device:
        return domain.Device(
            id=self.id,
            name=self.name,
            site_id=self.site_id,
            type=self.type,
        )
