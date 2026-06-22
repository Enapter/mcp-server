import dataclasses

from .access_role import AccessRole
from .command_argument_declaration import CommandArgumentDeclaration


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandDeclaration:
    name: str
    display_name: str
    access_level: AccessRole
    description: str | None
    arguments: list[CommandArgumentDeclaration]
    implements: list[str]
