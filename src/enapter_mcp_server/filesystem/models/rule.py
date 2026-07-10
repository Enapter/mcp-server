from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_script import RuleScript
from .rule_state import RuleState


class Rule(pydantic.BaseModel):
    id: str
    slug: str
    disabled: bool
    state: RuleState
    script: RuleScript

    @classmethod
    def from_domain(cls, rule: domain.Rule) -> Self:
        return cls(
            id=rule.id,
            slug=rule.slug,
            disabled=rule.disabled,
            state=rule.state.value,
            script=RuleScript.from_domain(rule.script),
        )

    def to_domain(self) -> domain.Rule:
        return domain.Rule(
            id=self.id,
            slug=self.slug,
            disabled=self.disabled,
            state=domain.RuleState(self.state),
            script=self.script.to_domain(),
        )
