import dataclasses
import re

from enapter_mcp_server import domain


@dataclasses.dataclass(kw_only=True)
class RuleSearchQuery:
    site_id: str
    rule_id: str | None = None
    slug_regexp: str | None = None

    def __post_init__(self) -> None:
        self._slug_pattern = (
            re.compile(self.slug_regexp) if self.slug_regexp is not None else None
        )

    def matches(self, rule: domain.Rule) -> bool:
        if self.rule_id is not None and rule.id != self.rule_id:
            return False
        if self._slug_pattern is not None and not self._slug_pattern.search(rule.slug):
            return False
        return True
