import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteDTO:
    id: str
    name: str
    timezone: str
