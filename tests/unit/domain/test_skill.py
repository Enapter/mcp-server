import pathlib

import pytest

from enapter_mcp_server import domain


class TestSkillRead:
    def test_returns_content_for_existing_file(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={
                pathlib.PurePosixPath("SKILL.md"): "content",
                pathlib.PurePosixPath("refs/guide.md"): "guide content",
            },
        )
        assert skill.read(pathlib.PurePosixPath("SKILL.md")) == "content"

    def test_normalizes_dot_slash_in_path(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={pathlib.PurePosixPath("references/v3/api.md"): "api content"},
        )
        assert (
            skill.read(pathlib.PurePosixPath("./references/v3/api.md")) == "api content"
        )

    def test_normalizes_dot_slash_against_normalized_keys(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={pathlib.PurePosixPath("SKILL.md"): "content"},
        )
        assert skill.read(pathlib.PurePosixPath("./SKILL.md")) == "content"

    def test_raises_skill_file_not_found_on_miss(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={
                pathlib.PurePosixPath("SKILL.md"): "content",
                pathlib.PurePosixPath("refs/guide.md"): "guide content",
            },
        )
        with pytest.raises(domain.SkillFileNotFound) as exc:
            skill.read(pathlib.PurePosixPath("nonexistent.md"))
        assert exc.value.path == pathlib.PurePosixPath("nonexistent.md")
        assert exc.value.valid == [
            pathlib.PurePosixPath("SKILL.md"),
            pathlib.PurePosixPath("refs/guide.md"),
        ]

    def test_traversal_attempt_is_not_normalized_key(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={pathlib.PurePosixPath("SKILL.md"): "content"},
        )
        with pytest.raises(domain.SkillFileNotFound):
            skill.read(pathlib.PurePosixPath("../SKILL.md"))

    def test_directory_form_is_not_normalized_key(self) -> None:
        skill = domain.Skill(
            name="enapter:rule-creator",
            files={pathlib.PurePosixPath("refs/guide.md"): "guide content"},
        )
        with pytest.raises(domain.SkillFileNotFound):
            skill.read(pathlib.PurePosixPath("refs/"))
