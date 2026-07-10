from typing import Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .site_status import SiteStatus


class Site(pydantic.BaseModel):
    id: str
    name: str
    timezone: str
    authorized_role: AccessRole
    status: SiteStatus | None = None

    @classmethod
    def from_domain(cls, site: domain.Site) -> Self:
        return cls(
            id=site.id,
            name=site.name,
            timezone=site.timezone,
            authorized_role=site.authorized_role.value,
            status=(
                SiteStatus.from_domain(site.status) if site.status is not None else None
            ),
        )

    def to_domain(self) -> domain.Site:
        return domain.Site(
            id=self.id,
            name=self.name,
            timezone=self.timezone,
            authorized_role=domain.AccessRole(self.authorized_role),
            status=(self.status.to_domain() if self.status is not None else None),
        )
