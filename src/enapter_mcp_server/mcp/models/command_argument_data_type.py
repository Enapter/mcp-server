import enum


class CommandArgumentDataType(enum.Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY_OF_STRINGS = "array_of_strings"
    OBJECT = "object"
