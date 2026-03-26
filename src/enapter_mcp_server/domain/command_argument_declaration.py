import dataclasses
from typing import Any

from .command_argument_data_type import CommandArgumentDataType


@dataclasses.dataclass(frozen=True, kw_only=True)
class CommandArgumentDeclaration:
    name: str
    display_name: str
    data_type: CommandArgumentDataType
    required: bool
    description: str | None
    enum: list[Any] | None
