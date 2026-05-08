import dataclasses

from .rule_script_summary import RuleScriptSummary
from .rule_state import RuleState


@dataclasses.dataclass(frozen=True, kw_only=True)
class Rule:
    id: str
    slug: str
    enabled: bool
    state: RuleState
    script_summary: RuleScriptSummary
