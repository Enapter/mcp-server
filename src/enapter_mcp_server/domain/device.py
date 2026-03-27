import dataclasses
from typing import Any

from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class Device:
    id: str
    name: str
    site_id: str
    type: DeviceType
    connectivity_status: ConnectivityStatus | None = None
    properties: dict[str, Any] | None = None
    active_alerts: list[str] | None = None
    blueprint_summary: BlueprintSummary | None = None
