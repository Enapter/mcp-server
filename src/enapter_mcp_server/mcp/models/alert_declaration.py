from typing import Self

import pydantic

from enapter_mcp_server import domain

from .alert_severity import AlertSeverity


class AlertDeclaration(pydantic.BaseModel):
    """Represents an alert declaration.

    An alert is a notification about a significant event or condition related to
    the device. Alerts can indicate issues, warnings, or informational messages.
    """

    name: str
    display_name: str
    severity: AlertSeverity
    description: str | None
    troubleshooting: list[str] | None
    components: list[str] | None
    conditions: list[str] | None

    @classmethod
    def from_domain(cls, declaration: domain.AlertDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            severity=declaration.severity.value,
            description=declaration.description,
            troubleshooting=declaration.troubleshooting,
            components=declaration.components,
            conditions=declaration.conditions,
        )
