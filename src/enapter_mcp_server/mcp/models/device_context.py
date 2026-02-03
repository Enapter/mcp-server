import datetime
from typing import Any

import pydantic

from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device import Device


class DeviceContext(pydantic.BaseModel):
    """Represents the context of a device.

    Device context includes metadata about the device, its connectivity status,
    properties, latest telemetry, and a summary of its blueprint.

    Attributes:
        timestamp: The timestamp when the context was recorded.
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
