import dataclasses

from .access_role import AccessRole
from .site_status import SiteStatus


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    id: str
    name: str
    timezone: str
    authorized_role: AccessRole
    status: SiteStatus | None = None

    def with_status(self, status: SiteStatus) -> "Site":
        return dataclasses.replace(self, status=status)
