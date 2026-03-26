from typing import Any, Self

import pydantic

from enapter_mcp_server import domain

from .data_type import DataType


class CommandArgumentDeclaration(pydantic.BaseModel):
    """A declaration of an argument for a device command."""

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
