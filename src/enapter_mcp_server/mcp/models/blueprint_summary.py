from typing import Self

import pydantic

from enapter_mcp_server import domain


class BlueprintSummary(pydantic.BaseModel):
    """A summary of a blueprint's key attributes.

    A blueprint is a specification that defines the integration between Enapter
    and a device. It outlines the available telemetry attributes, commands,
    properties, and alerts that the device supports. Every device has a
    blueprint assigned to it.
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
