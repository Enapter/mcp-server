from enapter_mcp_server import domain, filesystem

RULE_1 = "fffffff1-1111-1111-1111-111111111111"
RULE_2 = "fffffff2-2222-2222-2222-222222222222"
RULE_3 = "fffffff3-3333-3333-3333-333333333333"


class TestRuleModel:
    def test_round_trip(self) -> None:
        domain_rule = domain.Rule(
            id=RULE_1,
            slug="test-rule",
            disabled=True,
            state=domain.RuleState.STOPPED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval="60s",
                code='print("hello")',
            ),
        )

        model = filesystem.models.Rule.from_domain(domain_rule)
        result = model.to_domain()

        assert result == domain_rule

    def test_round_trip_no_exec_interval(self) -> None:
        domain_rule = domain.Rule(
            id=RULE_2,
            slug="simple-rule",
            disabled=False,
            state=domain.RuleState.STARTED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V1,
                exec_interval=None,
                code="",
            ),
        )

        model = filesystem.models.Rule.from_domain(domain_rule)
        result = model.to_domain()

        assert result == domain_rule

    def test_enum_conversion(self) -> None:
        domain_rule = domain.Rule(
            id=RULE_3,
            slug="enum-test",
            disabled=True,
            state=domain.RuleState.STOPPED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="local x = 1",
            ),
        )

        model = filesystem.models.Rule.from_domain(domain_rule)

        assert model.state == "stopped"
        assert model.script.runtime_version == "v3"
