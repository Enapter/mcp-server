import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandConfirmation:
    severity: str | None = None
    title: str | None = None
    description: str | None = None
