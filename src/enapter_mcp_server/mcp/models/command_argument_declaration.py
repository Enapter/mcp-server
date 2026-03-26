from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .data_type import DataType


class CommandArgumentDeclaration(pydantic.BaseModel):
    """A declaration of an argument for a device command.

    Attributes:
        name: The unique identifier for the argument within the command.
        display_name: A human-readable name for the argument.
        data_type: The data type of the argument's value.
        required: Whether the argument must be provided when executing the command.
        description: A brief explanation of the argument's purpose.
        enum: A list of possible values for the argument.
    """

    name: str
    display_name: str
    data_type: DataType
    required: bool
    description: str | None
    enum: list[Any] | None = None

    @classmethod
    def from_domain(cls, declaration: domain.CommandArgumentDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            data_type=declaration.data_type.value,
            required=declaration.required,
            description=declaration.description,
            enum=declaration.enum,
        )
