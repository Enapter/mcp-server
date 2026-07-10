from enapter_mcp_server import domain, filesystem

SITE_1 = "11111111-1111-1111-1111-111111111111"
SITE_2 = "22222222-2222-2222-2222-222222222222"
SITE_3 = "33333333-3333-3333-3333-333333333333"
RULE_1 = "fffffff1-1111-1111-1111-111111111111"
RULE_2 = "fffffff2-2222-2222-2222-222222222222"


class TestRuleEngineModel:
    def test_round_trip(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )

        model = filesystem.models.RuleEngine.from_domain(domain_engine)
        result = model.to_domain()

        assert result == domain_engine

    def test_round_trip_suspended(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_2,
            state=domain.RuleEngineState.SUSPENDED,
            timezone="Asia/Tokyo",
        )

        model = filesystem.models.RuleEngine.from_domain(domain_engine)
        result = model.to_domain()

        assert result == domain_engine

    def test_enum_conversion(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_3,
            state=domain.RuleEngineState.ACTIVE,
            timezone="Europe/Berlin",
        )

        model = filesystem.models.RuleEngine.from_domain(domain_engine)

        assert model.state == "active"
        assert isinstance(model.state, str)


class TestRuleEngineAggregateModel:
    def test_round_trip_with_rules(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
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

        engine_model = filesystem.models.RuleEngine.from_domain(domain_engine)
        rule_model = filesystem.models.Rule.from_domain(domain_rule)
        file_model = filesystem.models.RuleEngineAggregate(
            rule_engine=engine_model, rules=[rule_model]
        )

        data = file_model.model_dump(mode="json", exclude_none=True)
        loaded = filesystem.models.RuleEngineAggregate.model_validate(data)

        assert loaded.rule_engine.to_domain() == domain_engine
        assert len(loaded.rules) == 1
        assert loaded.rules[0].to_domain() == domain_rule

    def test_round_trip_no_rules(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )

        engine_model = filesystem.models.RuleEngine.from_domain(domain_engine)
        file_model = filesystem.models.RuleEngineAggregate(rule_engine=engine_model)

        data = file_model.model_dump(mode="json", exclude_none=True)
        loaded = filesystem.models.RuleEngineAggregate.model_validate(data)

        assert loaded.rule_engine.to_domain() == domain_engine
        assert loaded.rules == []

    def test_round_trip_multiple_rules(self) -> None:
        domain_engine = domain.RuleEngine(
            id=SITE_1,
            state=domain.RuleEngineState.ACTIVE,
            timezone="UTC",
        )
        rule1 = domain.Rule(
            id=RULE_1,
            slug="rule-1",
            disabled=True,
            state=domain.RuleState.STOPPED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="local x = 1",
            ),
        )
        rule2 = domain.Rule(
            id=RULE_2,
            slug="rule-2",
            disabled=False,
            state=domain.RuleState.STARTED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V1,
                exec_interval="10s",
                code="local y = 2",
            ),
        )

        engine_model = filesystem.models.RuleEngine.from_domain(domain_engine)
        rule1_model = filesystem.models.Rule.from_domain(rule1)
        rule2_model = filesystem.models.Rule.from_domain(rule2)
        file_model = filesystem.models.RuleEngineAggregate(
            rule_engine=engine_model, rules=[rule1_model, rule2_model]
        )

        data = file_model.model_dump(mode="json", exclude_none=True)
        loaded = filesystem.models.RuleEngineAggregate.model_validate(data)

        assert loaded.rule_engine.to_domain() == domain_engine
        assert len(loaded.rules) == 2
        assert {r.to_domain() for r in loaded.rules} == {rule1, rule2}
