import dataclasses
import functools
import re

from enapter_mcp_server import domain

from .device_dto import DeviceDTO


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceSearchQuery:
    device_id: str | None = None
    site_id: str | None = None
    device_type: domain.DeviceType | None = None
    name_pattern: str | None = None

    @functools.cached_property
    def _name_re(self) -> re.Pattern[str] | None:
        if self.name_pattern is None:
            return None
        return re.compile(self.name_pattern)

    def matches(self, device_dto: DeviceDTO) -> bool:
        if self.device_id is not None and device_dto.id != self.device_id:
            return False
        if self.device_type is not None and device_dto.type != self.device_type:
            return False
        if self.site_id is not None and device_dto.site_id != self.site_id:
            return False
        if self._name_re is not None and not self._name_re.search(device_dto.name):
            return False
        return True
