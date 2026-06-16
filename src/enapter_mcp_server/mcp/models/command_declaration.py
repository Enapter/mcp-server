from typing import Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .command_argument_declaration import CommandArgumentDeclaration


class CommandDeclaration(pydantic.BaseModel):
    """A declaration of a device command."""

    name: str
    display_name: str
    access_level: AccessRole
    description: str | None
    arguments: list[CommandArgumentDeclaration]

    @classmethod
    def from_domain(cls, declaration: domain.CommandDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            access_level=declaration.access_level.value,
            description=declaration.description,
            arguments=[
                CommandArgumentDeclaration.from_domain(a) for a in declaration.arguments
            ],
        )
