import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    id: str
    name: str
    timezone: str
