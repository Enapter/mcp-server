from typing import Protocol

from .rule import Rule
from .rule_script import RuleScript


class RuleManagementPolicy(Protocol):
    def assert_can_create(
        self,
        *,
        slug: str,
        script: RuleScript,
        disabled: bool,
    ) -> None: ...

    def assert_can_edit(self, rule: Rule) -> None: ...

    def assert_can_delete(self, rule: Rule) -> None: ...
