import dataclasses

from .rule_script import RuleScript
from .rule_state import RuleState

MCP_PREFIX = "mcp-"


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

    @property
    def is_mcp_managed(self) -> bool:
        return self.slug.startswith(MCP_PREFIX)
