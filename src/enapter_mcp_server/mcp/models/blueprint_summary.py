from typing import Self

import pydantic

from enapter_mcp_server import domain


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
        commands_total: The total number of commands defined in the blueprint.
        properties_total: The total number of properties defined in the blueprint.
        telemetry_attributes_total: The total number of telemetry attributes defined in the blueprint.
        alerts_total: The total number of alerts defined in the blueprint.
    """

    description: str | None
    vendor: str | None
    commands_total: int
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int

    @classmethod
    def from_domain(cls, blueprint_summary: domain.BlueprintSummary) -> Self:
        return cls(
            description=blueprint_summary.description,
            vendor=blueprint_summary.vendor,
            commands_total=blueprint_summary.commands_total,
            properties_total=blueprint_summary.properties_total,
            telemetry_attributes_total=blueprint_summary.telemetry_attributes_total,
            alerts_total=blueprint_summary.alerts_total,
        )
