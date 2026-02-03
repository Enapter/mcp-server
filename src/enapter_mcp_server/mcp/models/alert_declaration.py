from typing import Any, Self

import pydantic

from .alert_severity import AlertSeverity


class AlertDeclaration(pydantic.BaseModel):
    """Represents an alert declaration.

    Alert is a notification about a significant event or condition related to
    the device. Alerts can indicate issues, warnings, or informational messages.

    Attributes:
        name: The name of the alert.
        severity: The severity level of the alert.
        description: A description of the alert.
        troubleshooting: A list of troubleshooting steps for the alert.
        components: A list of device components related to the alert.
        conditions: A list of conditions that trigger the alert.
    """

    name: str
    severity: AlertSeverity
    description: str | None
    troubleshooting: list[str] | None
    components: list[str] | None
    conditions: list[str] | None

    @classmethod
    def from_dto(cls, name: str, dto: dict[str, Any]) -> Self:
        return cls(
            name=name,
            severity=AlertSeverity(dto["severity"]),
            description=dto.get("description"),
            troubleshooting=dto.get("troubleshooting"),
            components=dto.get("components"),
            conditions=dto.get("conditions"),
        )
