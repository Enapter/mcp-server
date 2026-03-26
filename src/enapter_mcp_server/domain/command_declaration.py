import dataclasses

from .command_argument_declaration import CommandArgumentDeclaration


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandDeclaration:
    name: str
    display_name: str
    description: str | None
    arguments: list[CommandArgumentDeclaration]
