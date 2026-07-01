import dataclasses
import re

from enapter_mcp_server import domain


@dataclasses.dataclass(kw_only=True)
class SiteSearchQuery:
    site_id: str | None = None
    name_regexp: str | None = None
    timezone_regexp: str | None = None

    def __post_init__(self) -> None:
        self._name_pattern = (
            re.compile(self.name_regexp) if self.name_regexp is not None else None
        )
        self._timezone_pattern = (
            re.compile(self.timezone_regexp)
            if self.timezone_regexp is not None
            else None
        )

    def matches(self, site: domain.Site) -> bool:
        if self.site_id is not None and site.id != self.site_id:
            return False
        if self._name_pattern is not None and not self._name_pattern.search(site.name):
            return False
        if self._timezone_pattern is not None and not self._timezone_pattern.search(
            site.timezone
        ):
            return False
        return True
