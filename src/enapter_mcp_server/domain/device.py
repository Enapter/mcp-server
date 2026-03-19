import dataclasses
from typing import Any

from .connectivity_status import ConnectivityStatus
from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class Device:
    id: str
    name: str
    site_id: str
    type: DeviceType
    connectivity: ConnectivityStatus | None = None
    properties: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
