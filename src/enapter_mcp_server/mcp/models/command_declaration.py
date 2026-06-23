from typing import Self

import pydantic

from enapter_mcp_server import domain

from .access_role import AccessRole
from .command_argument_declaration import CommandArgumentDeclaration
from .command_confirmation import CommandConfirmation


class CommandDeclaration(pydantic.BaseModel):
    """A declaration of a device command.

    The `access_level` field defines the minimum role required to execute this command. A user can execute this command only if their `authorized_role` for the device is at or after this `access_level`.

    The `confirmation` field, when present, marks the command as consequential per the vendor's declaration.
    """

    name: str
    display_name: str
    access_level: AccessRole
    description: str | None
    arguments: list[CommandArgumentDeclaration]
    implements: list[str]
    confirmation: CommandConfirmation | None = None

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
            implements=declaration.implements,
            confirmation=(
                CommandConfirmation.from_domain(declaration.confirmation)
                if declaration.confirmation is not None
                else None
            ),
        )
