from typing import Self

import enapter
import pydantic


class Site(pydantic.BaseModel):
    """Represents a site with its attributes.

    Site is a location or facility where devices are installed.

    Attributes:
        id: The unique identifier (UUID) of the site.
        name: The name of the site.
        timezone: The timezone of the site in the IANA Time Zone Identifier
            format. E.g. "Europe/Berlin".
    """

    id: str
    name: str
    timezone: str

    @classmethod
    def from_domain(cls, site: enapter.http.api.sites.Site) -> Self:
        return cls(id=site.id, name=site.name, timezone=site.timezone)
