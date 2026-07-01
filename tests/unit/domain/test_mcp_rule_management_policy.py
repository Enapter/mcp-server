import pytest

from enapter_mcp_server import domain


def make_rule(
    *,
    rule_id: str = "rule-1",
    slug: str = "mcp-test",
    disabled: bool = True,
    runtime_version: domain.RuleRuntimeVersion = domain.RuleRuntimeVersion.V3,
    code: str = "local x = 1\nreturn x",
) -> domain.Rule:
    return domain.Rule(
        id=rule_id,
        slug=slug,
        disabled=disabled,
        state=domain.RuleState.STOPPED,
        script=domain.RuleScript(
            runtime_version=runtime_version,
            exec_interval="2m",
            code=code,
        ),
    )


class TestMcpRuleManagementPolicy:
    def test_assert_can_create_accepts_managed_disabled_v3_rule(self) -> None:
        domain.McpRuleManagementPolicy().assert_can_create(
            slug="mcp-test",
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="local x = 1",
            ),
            disabled=True,
        )

    def test_assert_can_create_rejects_unmanaged_slug(self) -> None:
        with pytest.raises(domain.UnprefixedRuleSlug):
            domain.McpRuleManagementPolicy().assert_can_create(
                slug="test",
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="local x = 1",
                ),
                disabled=True,
            )

    def test_assert_can_create_rejects_non_v3_script(self) -> None:
        with pytest.raises(domain.RuleNotV3):
            domain.McpRuleManagementPolicy().assert_can_create(
                slug="mcp-test",
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V1,
                    exec_interval=None,
                    code="local x = 1",
                ),
                disabled=True,
            )

    def test_assert_can_create_rejects_enabled_rule(self) -> None:
        with pytest.raises(domain.RuleMustBeCreatedDisabled):
            domain.McpRuleManagementPolicy().assert_can_create(
                slug="mcp-test",
                script=domain.RuleScript(
                    runtime_version=domain.RuleRuntimeVersion.V3,
                    exec_interval=None,
                    code="local x = 1",
                ),
                disabled=False,
            )

    def test_assert_can_edit_accepts_disabled_mcp_v3_rule(self) -> None:
        domain.McpRuleManagementPolicy().assert_can_edit(make_rule())

    def test_assert_can_edit_rejects_enabled_rule(self) -> None:
        with pytest.raises(domain.RuleNotDisabled):
            domain.McpRuleManagementPolicy().assert_can_edit(make_rule(disabled=False))

    def test_assert_can_edit_rejects_unmanaged_rule(self) -> None:
        with pytest.raises(domain.RuleNotMcpManaged):
            domain.McpRuleManagementPolicy().assert_can_edit(make_rule(slug="test"))

    def test_assert_can_edit_rejects_non_v3_rule(self) -> None:
        with pytest.raises(domain.RuleNotV3):
            domain.McpRuleManagementPolicy().assert_can_edit(
                make_rule(runtime_version=domain.RuleRuntimeVersion.V1)
            )

    def test_assert_can_delete_accepts_disabled_mcp_rule(self) -> None:
        domain.McpRuleManagementPolicy().assert_can_delete(make_rule())

    def test_assert_can_delete_rejects_enabled_rule(self) -> None:
        with pytest.raises(domain.RuleNotDisabled):
            domain.McpRuleManagementPolicy().assert_can_delete(
                make_rule(disabled=False)
            )

    def test_assert_can_delete_rejects_unmanaged_rule(self) -> None:
        with pytest.raises(domain.RuleNotMcpManaged):
            domain.McpRuleManagementPolicy().assert_can_delete(make_rule(slug="test"))
