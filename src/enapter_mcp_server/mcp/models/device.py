from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


class Device(pydantic.BaseModel):
    """Represents a device.

    An individual unit that can be monitored and controlled.

    The `authorized_role` field indicates the authenticated user's access
    level for this device. For property values, telemetry data, and command
    execution, a user can read the value (or execute the command) only if
    their `authorized_role` is at or after the declaration's `access_level`.
    """

    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType
    authorized_role: AccessRole
    blueprint_summary: BlueprintSummary
    connectivity_status: ConnectivityStatus
    active_alerts_total: int
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None

    @classmethod
    def from_domain(cls, device: domain.Device) -> Self:
        return cls(
            id=device.id,
            blueprint_id=device.blueprint_id,
            name=device.name,
            site_id=device.site_id,
            type=device.type.value,
            authorized_role=device.authorized_role.value,
            connectivity_status=device.connectivity_status.value,
            active_alerts_total=device.active_alerts_total,
            properties=device.properties,
            active_alerts=device.active_alerts,
            blueprint_summary=BlueprintSummary.from_domain(device.blueprint_summary),
        )
