import dataclasses

from .rule_engine_state import RuleEngineState


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleEngine:
    id: str
    state: RuleEngineState
    timezone: str
