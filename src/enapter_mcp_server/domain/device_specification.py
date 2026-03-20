import dataclasses

from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceSpecification:
    site_id: str | None = None
    device_type: DeviceType | None = None
    name_pattern: str = ".*"
