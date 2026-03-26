import datetime
from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device import Device


class DeviceDetails(pydantic.BaseModel):
    """Represents the details of a device.

    Device details include metadata about the device, its connectivity status,
    properties, currently active alerts, and a summary of its blueprint.
    """

    timestamp: datetime.datetime
    device: Device
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any]
    active_alerts: list[str]
    blueprint_summary: BlueprintSummary

    @classmethod
    def from_domain(cls, details: domain.DeviceDetails) -> Self:
        return cls(
            timestamp=details.timestamp,
            device=Device.from_domain(details.device),
            connectivity_status=details.connectivity_status.value,
            properties=details.properties,
            active_alerts=details.active_alerts,
            blueprint_summary=BlueprintSummary.from_domain(details.blueprint_summary),
        )
