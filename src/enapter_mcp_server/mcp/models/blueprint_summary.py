from typing import Any, Self

import pydantic


class BlueprintSummary(pydantic.BaseModel):
    """
    A summary of a blueprint's key attributes.

    A blueprint is a specification that defines the integration between Enapter
    and a device. It outlines the available telemetry attributes, commands,
    properties, and alerts that the device supports. Every device has a
    blueprint assigned to it.

    Attributes:
        description: A brief description of the device.
        vendor: The vendor of the device.
        properties_total: The total number of properties defined in the blueprint.
        telemetry_attributes_total: The total number of telemetry attributes defined in the blueprint.
        alerts_total: The total number of alerts defined in the blueprint.
    """

    description: str | None
    vendor: str | None
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any]) -> Self:
        return cls(
            description=manifest.get("description"),
            vendor=manifest.get("vendor"),
            properties_total=len(manifest.get("properties", {})),
            telemetry_attributes_total=len(manifest.get("telemetry", {})),
            alerts_total=len(manifest.get("alerts", {})),
        )
