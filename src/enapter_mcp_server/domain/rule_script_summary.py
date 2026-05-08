import dataclasses

from .rule_runtime_version import RuleRuntimeVersion


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleScriptSummary:
    runtime_version: RuleRuntimeVersion
    exec_interval: str | None
    lines_count: int
