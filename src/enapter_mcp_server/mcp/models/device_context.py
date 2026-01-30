import datetime
from typing import Any

import pydantic

from .connectivity_status import ConnectivityStatus
from .device import Device


class DeviceContext(pydantic.BaseModel):
    """Represents the context of a device.

    Device context includes information about the device itself, its connectivity
    status, properties, and the latest telemetry data.

    Attributes:
        timestamp: The timestamp when the context was recorded.
        device: The device information.
        connectivity_status: The connectivity status of the device.
        properties: A dictionary of device properties. Device property is
            metadata which does not change during normal operation, e.g.
            `firmware_version`, `model`, and `serial_number`.
        latest_telemetry: A dictionary of the latest telemetry data from the device.
    """

    timestamp: datetime.datetime
    device: Device
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any]
    latest_telemetry: dict[str, Any]
