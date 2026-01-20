from typing import Self

import enapter
import pydantic


class Site(pydantic.BaseModel):

    id: str
    name: str
    timezone: str

    @classmethod
    def from_domain(cls, site: enapter.http.api.sites.Site) -> Self:
        return cls(id=site.id, name=site.name, timezone=site.timezone)
