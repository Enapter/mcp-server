import dataclasses
from typing import Any

from .access_role import AccessRole
from .blueprint_summary import BlueprintSummary
from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class Device:
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
