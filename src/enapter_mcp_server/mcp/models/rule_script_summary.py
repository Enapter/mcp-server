from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_runtime_version import RuleRuntimeVersion


class RuleScriptSummary(pydantic.BaseModel):
    """Metadata about a rule's underlying Lua script.

    Contains execution details and the size of the script, but does not
    include the script source code itself.
    """

    runtime_version: RuleRuntimeVersion
    exec_interval: str | None
    lines_count: int

    @classmethod
    def from_domain(cls, summary: domain.RuleScriptSummary) -> Self:
        return cls(
            runtime_version=summary.runtime_version.value,
            exec_interval=summary.exec_interval,
            lines_count=summary.lines_count,
        )
