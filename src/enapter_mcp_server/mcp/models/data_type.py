import enum


class DataType(enum.StrEnum):
    """Represents the data type of a property or telemetry attribute."""

    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY_OF_STRINGS = "array_of_strings"
    OBJECT = "object"
