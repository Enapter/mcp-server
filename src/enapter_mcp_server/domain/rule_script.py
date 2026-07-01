import dataclasses

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
