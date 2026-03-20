import dataclasses
import functools
import re

from .site import Site


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteSpecification:
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

    def matches(self, site: Site) -> bool:
        if self._name_re is not None and not self._name_re.search(site.name):
            return False
        if self._timezone_re is not None and not self._timezone_re.search(site.timezone):
            return False
        return True

