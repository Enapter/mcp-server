from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_engine_state import RuleEngineState


class RuleEngine(pydantic.BaseModel):
    id: str
    state: RuleEngineState
    timezone: str

    @classmethod
    def from_domain(cls, engine: domain.RuleEngine) -> Self:
        return cls(
            id=engine.id,
            state=engine.state.value,
            timezone=engine.timezone,
        )

    def to_domain(self) -> domain.RuleEngine:
        return domain.RuleEngine(
            id=self.id,
            state=domain.RuleEngineState(self.state),
            timezone=self.timezone,
        )
