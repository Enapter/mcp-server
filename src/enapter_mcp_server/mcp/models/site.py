from typing import Self

import pydantic

from enapter_mcp_server import domain


class Site(pydantic.BaseModel):
    """Represents a site.

    A location or facility where devices are installed.
    """

    id: str
    name: str
    timezone: str

    @classmethod
    def from_domain(cls, site: domain.Site) -> Self:
        return cls(id=site.id, name=site.name, timezone=site.timezone)
