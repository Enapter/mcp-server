import dataclasses
import functools
import re

from .site_dto import SiteDTO


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteSearchQuery:
    site_id: str | None = None
    name_regexp: str | None = None
    timezone_regexp: str | None = None

    @functools.cached_property
    def _name_pattern(self) -> re.Pattern[str] | None:
        if self.name_regexp is None:
            return None
        return re.compile(self.name_regexp)

    @functools.cached_property
    def _timezone_pattern(self) -> re.Pattern[str] | None:
        if self.timezone_regexp is None:
            return None
        return re.compile(self.timezone_regexp)

    def matches(self, site_dto: SiteDTO) -> bool:
        if self.site_id is not None and site_dto.id != self.site_id:
            return False
        if self._name_pattern is not None and not self._name_pattern.search(
            site_dto.name
        ):
            return False
        if self._timezone_pattern is not None and not self._timezone_pattern.search(
            site_dto.timezone
        ):
            return False
        return True
