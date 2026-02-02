import enum


class PropertyDataType(enum.StrEnum):
    """Represents the data type of a device property."""

    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY_OF_STRINGS = "array_of_strings"
    OBJECT = "object"
