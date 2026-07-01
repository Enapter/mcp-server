from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_script_summary import RuleScriptSummary
from .rule_state import RuleState


class Rule(pydantic.BaseModel):
    """Represents an automation rule on the Enapter Rule Engine.

    Rules are Lua scripts executed on a site's Gateway to implement custom
    logic, automation, and integrations between different devices.
    """

    id: str
    slug: str
    enabled: bool
    state: RuleState
    script_summary: RuleScriptSummary

    @classmethod
    def from_domain(cls, rule: domain.Rule) -> Self:
        return cls(
            id=rule.id,
            slug=rule.slug,
            enabled=rule.enabled,
            state=rule.state.value,
            script_summary=RuleScriptSummary.from_domain(rule.script.summary),
        )
