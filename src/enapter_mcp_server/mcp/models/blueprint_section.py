import enum


class BlueprintSection(enum.StrEnum):
    """Enum representing different sections of a blueprint.

    Attributes:
        TELEMETRY: Telemetry section of the blueprint.
        PROPERTIES: Properties section of the blueprint.
        ALERTS: Alerts section of the blueprint.
    """

    TELEMETRY = "telemetry"
    PROPERTIES = "properties"
    ALERTS = "alerts"
