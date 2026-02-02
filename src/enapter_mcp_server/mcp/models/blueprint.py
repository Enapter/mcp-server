from typing import Any, Self

import pydantic

from .alert_declaration import AlertDeclaration
from .property_declaration import PropertyDeclaration
from .telemetry_attribute_declaration import TelemetryAttributeDeclaration


class Blueprint(pydantic.BaseModel):
    """Represents a device blueprint.

    A blueprint is a specification that defines the integration between Enapter
    and a device. It outlines the available telemetry attributes, commands,
    properties, and alerts that the device supports. Every device has a
    blueprint assigned to it.

    Attributes:
        properties: A dictionary mapping property names to their corresponding
            declarations.
        telemetry: A dictionary mapping telemetry attribute names to their
            corresponding declarations.
        alerts: A dictionary mapping alert names to their corresponding
            declarations.
        description: A brief description of the device.
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
