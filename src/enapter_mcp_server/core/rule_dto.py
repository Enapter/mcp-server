import dataclasses

from enapter_mcp_server import domain


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuleDTO:
    id: str
    slug: str
    disabled: bool
    state: domain.RuleState
    script_runtime_version: domain.RuleRuntimeVersion
    script_exec_interval: str | None
    script_code: str

    def to_domain(self) -> domain.Rule:
        return domain.Rule(
            id=self.id,
            slug=self.slug,
            enabled=not self.disabled,
            state=self.state,
            script_summary=domain.RuleScriptSummary(
                runtime_version=self.script_runtime_version,
                exec_interval=self.script_exec_interval,
                lines_count=len(self.script_code.splitlines()),
            ),
        )
