import enum


class TelemetryAttributeDataType(enum.StrEnum):
    """Represents the data type of a telemetry attribute."""

    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY_OF_STRINGS = "array_of_strings"
    OBJECT = "object"
    ALERTS = "alerts"
