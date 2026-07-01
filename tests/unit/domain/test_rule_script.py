import pytest

from enapter_mcp_server import domain


class TestRuleScript:
    def test_replace_once_replaces_unique_match_preserving_metadata(self) -> None:
        script = domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval="2m",
            code="local x = 1\nreturn x",
        )

        updated = script.replace_once(
            old_string="local x = 1",
            new_string="local x = 2",
            rule_id="rule-1",
        )

        assert updated.runtime_version == domain.RuleRuntimeVersion.V3
        assert updated.exec_interval == "2m"
        assert updated.code == "local x = 2\nreturn x"

    def test_replace_once_rejects_empty_old_string(self) -> None:
        script = self._make_script("local x = 1")

        with pytest.raises(domain.EmptyRuleOldString):
            script.replace_once(old_string="", new_string="x", rule_id="rule-1")

    def test_replace_once_rejects_no_op(self) -> None:
        script = self._make_script("local x = 1")

        with pytest.raises(domain.NoOpRuleEdit):
            script.replace_once(old_string="x", new_string="x", rule_id="rule-1")

    def test_replace_once_rejects_missing_match(self) -> None:
        script = self._make_script("local x = 1")

        with pytest.raises(domain.RuleOldStringNotFound):
            script.replace_once(old_string="y", new_string="z", rule_id="rule-1")

    def test_replace_once_rejects_ambiguous_match(self) -> None:
        script = self._make_script("local x = 1\nlocal x = 2")

        with pytest.raises(domain.AmbiguousRuleOldString):
            script.replace_once(
                old_string="local x", new_string="local y", rule_id="rule-1"
            )

    @staticmethod
    def _make_script(code: str) -> domain.RuleScript:
        return domain.RuleScript(
            runtime_version=domain.RuleRuntimeVersion.V3,
            exec_interval=None,
            code=code,
        )
