from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


class Device(pydantic.BaseModel):
    """Represents a device.

    An individual unit that can be monitored and controlled.
    """

    id: str
    name: str
    site_id: str
    type: DeviceType
    blueprint_summary: BlueprintSummary
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None

    @classmethod
    def from_domain(cls, device: domain.Device) -> Self:
        return cls(
            id=device.id,
            name=device.name,
            site_id=device.site_id,
            type=device.type.value,
            connectivity_status=device.connectivity_status.value,
            properties=device.properties,
            active_alerts=device.active_alerts,
            blueprint_summary=BlueprintSummary.from_domain(device.blueprint_summary),
        )
