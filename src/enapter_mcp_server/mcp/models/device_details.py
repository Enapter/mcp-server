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
    properties, latest telemetry, and a summary of its blueprint.

    Attributes:
        timestamp: The timestamp when the details were recorded.
        device: The device information.
        connectivity_status: The connectivity status of the device.
        properties: A dictionary of device properties. Device property is
            metadata which does not change during normal operation, e.g.
            `firmware_version`, `model`, and `serial_number`.
        latest_telemetry: A dictionary of the latest telemetry data from the device.
        blueprint_summary: A summary of the device's blueprint.
    """

    timestamp: datetime.datetime
    device: Device
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any]
    latest_telemetry: dict[str, Any]
    blueprint_summary: BlueprintSummary

    @classmethod
    def from_domain(cls, details: domain.DeviceDetails) -> Self:
        return cls(
            timestamp=details.timestamp,
            device=Device.from_domain(details.device),
            connectivity_status=details.connectivity_status.value,
            properties=details.properties,
            latest_telemetry=details.latest_telemetry,
            blueprint_summary=BlueprintSummary.from_domain(details.blueprint_summary),
        )
