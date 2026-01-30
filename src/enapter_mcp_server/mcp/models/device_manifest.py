from typing import Any, Self

import pydantic

from .alert_declaration import AlertDeclaration
from .property_declaration import PropertyDeclaration
from .telemetry_attribute_declaration import TelemetryAttributeDeclaration


class DeviceManifest(pydantic.BaseModel):
    """Represents a device manifest.

    Device manifest defines the capabilities and characteristics of a device,
    including its properties, telemetry attributes, and alerts.

    Attributes:
        properties: A dictionary mapping property names to their corresponding
            declarations.
        telemetry: A dictionary mapping telemetry attribute names to their
            corresponding declarations.
        alerts: A dictionary mapping alert names to their corresponding
            declarations.
        description: A description of the device manifest.
        vendor: The vendor of the device.
    """

    properties: dict[str, PropertyDeclaration]
    telemetry: dict[str, TelemetryAttributeDeclaration]
    alerts: dict[str, AlertDeclaration]
    description: str | None
    vendor: str | None

    @classmethod
    def from_dto(cls, dto: dict[str, Any]) -> Self:
        return cls(
            properties={
                k: PropertyDeclaration.from_dto(v)
                for k, v in dto.get("properties", {}).items()
            },
            telemetry={
                k: TelemetryAttributeDeclaration.from_dto(v)
                for k, v in dto.get("telemetry", {}).items()
            },
            alerts={
                k: AlertDeclaration.from_dto(value)
                for k, value in dto.get("alerts", {}).items()
            },
            description=dto.get("description"),
            vendor=dto.get("vendor"),
        )
