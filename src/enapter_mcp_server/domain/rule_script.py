import dataclasses

from .errors import (
    AmbiguousRuleOldString,
    EmptyRuleOldString,
    NoOpRuleEdit,
    RuleOldStringNotFound,
)
from .rule_runtime_version import RuleRuntimeVersion
from .rule_script_summary import RuleScriptSummary


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleScript:
    runtime_version: RuleRuntimeVersion
    exec_interval: str | None
    code: str

    @property
    def summary(self) -> RuleScriptSummary:
        return RuleScriptSummary(
            runtime_version=self.runtime_version,
            exec_interval=self.exec_interval,
            lines_count=len(self.code.splitlines()),
        )

    def replace_once(
        self,
        *,
        old_string: str,
        new_string: str,
        rule_id: str,
    ) -> "RuleScript":
        if old_string == "":
            raise EmptyRuleOldString(
                "An empty old_string is not allowed. Provide the exact"
                " snippet of the current script you wish to replace."
            )
        if old_string == new_string:
            raise NoOpRuleEdit(
                "The old_string and new_string are identical. This"
                " would not change the rule's script."
            )

        count = self.code.count(old_string)
        if count == 0:
            raise RuleOldStringNotFound(
                f"The old_string was not found anywhere in the"
                f" current script of rule {rule_id!r}. The script may"
                f" have been changed; use read_rule to get the latest"
                f" content."
            )
        if count > 1:
            raise AmbiguousRuleOldString(
                f"The old_string appears {count} times in the"
                f" current script of rule {rule_id!r}. Include more"
                f" surrounding context to make the match unique."
            )

        return dataclasses.replace(
            self,
            code=self.code.replace(old_string, new_string, 1),
        )
