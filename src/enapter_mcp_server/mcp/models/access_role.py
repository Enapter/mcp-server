from typing import Annotated, Literal

import pydantic

AccessRole = Annotated[
    Literal["readonly", "user", "owner", "installer", "vendor", "system"],
    pydantic.Field(
        description="Roles in priority order: readonly < user < owner < installer < vendor < system."
    ),
]
