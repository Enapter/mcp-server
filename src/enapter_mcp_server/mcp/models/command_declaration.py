from typing import Self

import pydantic

from enapter_mcp_server import domain

from .command_argument_declaration import CommandArgumentDeclaration


class CommandDeclaration(pydantic.BaseModel):
    """A declaration of a device command."""

    name: str
    display_name: str
    description: str | None
    arguments: list[CommandArgumentDeclaration]

    @classmethod
    def from_domain(cls, declaration: domain.CommandDeclaration) -> Self:
        return cls(
            name=declaration.name,
            display_name=declaration.display_name,
            description=declaration.description,
            arguments=[
                CommandArgumentDeclaration.from_domain(a) for a in declaration.arguments
            ],
        )
