from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


class Device(pydantic.BaseModel):
    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType
    authorized_role: AccessRole
    slug: str | None = None
    connectivity: ConnectivityStatus | None = None
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None
    manifest: dict[str, Any] | None = None

    @classmethod
    def from_domain(cls, device: domain.Device) -> Self:
        return cls(
            id=device.id,
            blueprint_id=device.blueprint_id,
            name=device.name,
            site_id=device.site_id,
            type=device.type.value,
            authorized_role=device.authorized_role.value,
            connectivity=(
                device.connectivity.value if device.connectivity is not None else None
            ),
            properties=device.properties,
            active_alerts=device.active_alerts,
        )

    def to_domain(self) -> domain.Device:
        return domain.Device(
            id=self.id,
            blueprint_id=self.blueprint_id,
            name=self.name,
            site_id=self.site_id,
            type=domain.DeviceType(self.type),
            authorized_role=domain.AccessRole(self.authorized_role),
            connectivity=(
                domain.ConnectivityStatus(self.connectivity)
                if self.connectivity is not None
                else None
            ),
            properties=self.properties,
            active_alerts=self.active_alerts,
            manifest=None,
        )
