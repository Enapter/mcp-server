import dataclasses

from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class Device:
    id: str
    name: str
    site_id: str
    type: DeviceType
