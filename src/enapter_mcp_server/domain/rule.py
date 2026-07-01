import dataclasses

from .rule_script import RuleScript
from .rule_state import RuleState


@dataclasses.dataclass(frozen=True, kw_only=True)
class Rule:
    id: str
    slug: str
    disabled: bool
    state: RuleState
    script: RuleScript

    @property
    def enabled(self) -> bool:
        return not self.disabled
