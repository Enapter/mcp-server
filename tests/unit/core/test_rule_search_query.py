import re

import pytest

from enapter_mcp_server import core, domain


class TestRuleSearchQuery:
    def test_matches_site_id(self) -> None:
        # RuleSearchQuery handles site_id filtering by being passed to list_rules,
        # but it can also filter by rule_id and slug_regexp.
        rule = domain.Rule(
            id="r1",
            slug="alpha",
            disabled=False,
            state=domain.RuleState.STARTED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="",
            ),
        )

        query = core.RuleSearchQuery(site_id="s1", rule_id="r1")
        assert query.matches(rule) is True

        query = core.RuleSearchQuery(site_id="s1", rule_id="r2")
        assert query.matches(rule) is False

    def test_matches_slug_regexp(self) -> None:
        rule = domain.Rule(
            id="r1",
            slug="alpha-test",
            disabled=False,
            state=domain.RuleState.STARTED,
            script=domain.RuleScript(
                runtime_version=domain.RuleRuntimeVersion.V3,
                exec_interval=None,
                code="",
            ),
        )

        assert (
            core.RuleSearchQuery(site_id="s1", slug_regexp="alpha").matches(rule)
            is True
        )
        assert (
            core.RuleSearchQuery(site_id="s1", slug_regexp="test$").matches(rule)
            is True
        )
        assert (
            core.RuleSearchQuery(site_id="s1", slug_regexp="beta").matches(rule)
            is False
        )

    def test_invalid_regexp(self) -> None:
        with pytest.raises(re.error):
            core.RuleSearchQuery(site_id="s1", slug_regexp="[")
