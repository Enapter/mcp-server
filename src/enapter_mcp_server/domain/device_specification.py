import dataclasses
import functools
import re

from .device import Device
from .device_type import DeviceType


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceSpecification:
    site_id: str | None = None
    device_type: DeviceType | None = None
    name_pattern: str | None = None

    @functools.cached_property
    def _name_re(self) -> re.Pattern[str] | None:
        if self.name_pattern is None:
            return None
        return re.compile(self.name_pattern)

    def matches(self, device: Device) -> bool:
        if self.device_type is not None and device.type != self.device_type:
            return False
        if self.site_id is not None and device.site_id != self.site_id:
            return False
        if self._name_re is not None and not self._name_re.search(device.name):
            return False
        return True

