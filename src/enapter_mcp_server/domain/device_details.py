import dataclasses
import datetime
from typing import Any

from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device import Device


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceDetails:
    timestamp: datetime.datetime
    device: Device
    connectivity_status: ConnectivityStatus
    properties: dict[str, Any]
    latest_telemetry: dict[str, Any]
    blueprint_summary: BlueprintSummary
