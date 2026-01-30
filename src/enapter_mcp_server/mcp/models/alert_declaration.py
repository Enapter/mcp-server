from typing import Any, Self

import pydantic

from .alert_severity import AlertSeverity


class AlertDeclaration(pydantic.BaseModel):
    """Represents an alert declaration.

    Alert is a notification about a significant event or condition related to
    the device. Alerts can indicate issues, warnings, or informational messages.

    Attributes:
        severity: The severity level of the alert.
        description: A description of the alert.
        troubleshooting: A list of troubleshooting steps for the alert.
        components: A list of device components related to the alert.
        conditions: A list of conditions that trigger the alert.
    """

    severity: AlertSeverity
    description: str | None
    troubleshooting: list[str] | None
    components: list[str] | None
    conditions: list[str] | None

    @classmethod
    def from_dto(cls, dto: dict[str, Any]) -> Self:
        return cls(
            severity=AlertSeverity(dto["severity"]),
            description=dto.get("description"),
            troubleshooting=dto.get("troubleshooting"),
            components=dto.get("components"),
            conditions=dto.get("conditions"),
        )
