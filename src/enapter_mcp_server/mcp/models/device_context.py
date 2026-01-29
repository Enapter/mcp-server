from typing import Any

import pydantic

from .connectivity_status import ConnectivityStatus
from .device import Device


class DeviceContext(pydantic.BaseModel):
    """Represents the context of a device.

    Device context includes information about the device itself, its connectivity
    status, properties, and the latest telemetry data.

    Device properties is metadata which does not change during normal
    operation, e.g. `firmware_version`, `model`, and `serial_number`.

    Attributes:
        device: The device information.
        connectivity_status: The connectivity status of the device.
        properties: A dictionary of device properties.
        latest_telemetry: A dictionary of the latest telemetry data from the device.
    """

    device: Device
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any]
    latest_telemetry: dict[str, Any]
