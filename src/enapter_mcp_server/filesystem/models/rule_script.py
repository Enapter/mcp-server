from typing import Self

import pydantic

from enapter_mcp_server import domain

from .rule_runtime_version import RuleRuntimeVersion


class RuleScript(pydantic.BaseModel):
    runtime_version: RuleRuntimeVersion
    exec_interval: str | None = None
    code: str

    @classmethod
    def from_domain(cls, script: domain.RuleScript) -> Self:
        return cls(
            runtime_version=script.runtime_version.value,
            exec_interval=script.exec_interval,
            code=script.code,
        )

    def to_domain(self) -> domain.RuleScript:
        return domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion(self.runtime_version),
            exec_interval=self.exec_interval,
            code=self.code,
        )
