import dataclasses
import functools
import re

from .site_dto import SiteDTO


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteSearchQuery:
    site_id: str | None = None
    name_pattern: str | None = None
    timezone_pattern: str | None = None

    @functools.cached_property
    def _name_re(self) -> re.Pattern[str] | None:
        if self.name_pattern is None:
            return None
        return re.compile(self.name_pattern)

    @functools.cached_property
    def _timezone_re(self) -> re.Pattern[str] | None:
        if self.timezone_pattern is None:
            return None
        return re.compile(self.timezone_pattern)

    def matches(self, site_dto: SiteDTO) -> bool:
        if self.site_id is not None and site_dto.id != self.site_id:
            return False
        if self._name_re is not None and not self._name_re.search(site_dto.name):
            return False
        if self._timezone_re is not None and not self._timezone_re.search(
            site_dto.timezone
        ):
            return False
        return True
