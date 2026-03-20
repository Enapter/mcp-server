import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class SiteSpecification:
    name_pattern: str = ".*"
    timezone_pattern: str = ".*"
