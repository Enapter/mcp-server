from typing import Self

import pydantic

from enapter_mcp_server import domain


class CommandConfirmation(pydantic.BaseModel):
    """Vendor-declared confirmation block for a consequential command."""

    severity: str | None = None
    title: str | None = None
    description: str | None = None

    @classmethod
    def from_domain(cls, confirmation: domain.CommandConfirmation) -> Self:
        return cls(
            severity=confirmation.severity,
            title=confirmation.title,
            description=confirmation.description,
        )
