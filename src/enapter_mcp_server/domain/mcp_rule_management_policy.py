import dataclasses

from .errors import (
    RuleMustBeCreatedDisabled,
    RuleNotDisabled,
    RuleNotMCPManaged,
    RuleNotV3,
    UnprefixedRuleSlug,
)
from .rule import Rule
from .rule_runtime_version import RuleRuntimeVersion
from .rule_script import RuleScript

MCP_PREFIX = "mcp-"


@dataclasses.dataclass(frozen=True, kw_only=True)
class MCPRuleManagementPolicy:
    slug_prefix: str = MCP_PREFIX
    runtime_version: RuleRuntimeVersion = RuleRuntimeVersion.V3

    def assert_can_create(
        self,
        *,
        slug: str,
        script: RuleScript,
        disabled: bool,
    ) -> None:
        self._assert_managed_slug(slug)
        self._assert_v3_script(script)
        if not disabled:
            raise RuleMustBeCreatedDisabled(
                "MCP-managed rules must be created disabled so a human"
                " can review and enable them."
            )

    def assert_can_edit(self, rule: Rule) -> None:
        self._assert_disabled_for(rule, "editing")
        self._assert_managed_rule(rule)
        self._assert_v3_script(rule.script, rule_id=rule.id)

    def assert_can_delete(self, rule: Rule) -> None:
        self._assert_disabled_for(rule, "deleting")
        self._assert_managed_rule(rule)

    def _assert_managed_slug(self, slug: str) -> None:
        if not slug.startswith(self.slug_prefix):
            raise UnprefixedRuleSlug(
                f"The slug {slug!r} does not start with the MCP-managed"
                f" prefix {self.slug_prefix!r}."
            )

    def _assert_disabled_for(self, rule: Rule, action: str) -> None:
        if not rule.disabled:
            raise RuleNotDisabled(
                f"Rule {rule.id!r} is enabled. Please disable it in"
                f" the Enapter UI before {action} it via MCP."
            )

    def _assert_managed_rule(self, rule: Rule) -> None:
        if not rule.slug.startswith(self.slug_prefix):
            raise RuleNotMCPManaged(
                f"Rule {rule.id!r} has slug {rule.slug!r}, which"
                f" does not start with the MCP-managed prefix"
                f" {self.slug_prefix!r}."
            )

    def _assert_v3_script(
        self,
        script: RuleScript,
        rule_id: str | None = None,
    ) -> None:
        if script.runtime_version == self.runtime_version:
            return

        if rule_id is None:
            raise RuleNotV3(
                f"Rule script uses runtime version"
                f" {script.runtime_version.value!r}, but MCP rule"
                f" management only supports v3 rules."
            )
        raise RuleNotV3(
            f"Rule {rule_id!r} uses runtime version"
            f" {script.runtime_version.value!r}, but"
            f" rule management only supports v3 rules."
        )
