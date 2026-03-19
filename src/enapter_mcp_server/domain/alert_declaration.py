import dataclasses

from .alert_severity import AlertSeverity


@dataclasses.dataclass(frozen=True, kw_only=True)
class AlertDeclaration:
    name: str
    display_name: str
    severity: AlertSeverity
    description: str | None
    troubleshooting: list[str] | None
    components: list[str] | None
    conditions: list[str] | None
