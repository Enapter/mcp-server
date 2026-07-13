import pathlib

import pytest

from enapter_mcp_server import domain, filesystem


class TestSkillProvider:
    def test_from_directory_loads_namespaced_skill(
        self, tmp_path: pathlib.Path
    ) -> None:
        skill_dir = tmp_path / "enapter" / "skills" / "rule-creator"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill Index")
        (skill_dir / "refs").mkdir()
        (skill_dir / "refs" / "guide.md").write_text("Guide content")

        provider = filesystem.SkillProvider.from_directory(tmp_path)
        skill = provider.load_skill("enapter:rule-creator")

        assert skill.name == "enapter:rule-creator"
        assert skill.files == {
            pathlib.PurePosixPath("SKILL.md"): "# Skill Index",
            pathlib.PurePosixPath("refs/guide.md"): "Guide content",
        }

    def test_load_skill_raises_skill_not_found_for_unknown_name(
        self, tmp_path: pathlib.Path
    ) -> None:
        skill_dir = tmp_path / "enapter" / "skills" / "rule-creator"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Index")

        provider = filesystem.SkillProvider.from_directory(tmp_path)

        with pytest.raises(domain.SkillNotFound) as exc:
            provider.load_skill("nonexistent")
        assert exc.value.name == "nonexistent"

    def test_empty_provider_raises_skill_not_found(self) -> None:
        provider = filesystem.SkillProvider()

        with pytest.raises(domain.SkillNotFound) as exc:
            provider.load_skill("enapter:rule-creator")
        assert exc.value.name == "enapter:rule-creator"

    def test_from_directory_raises_when_path_does_not_exist(
        self, tmp_path: pathlib.Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            filesystem.SkillProvider.from_directory(tmp_path / "nonexistent")

    def test_from_directory_raises_when_path_is_file_not_directory(
        self, tmp_path: pathlib.Path
    ) -> None:
        file_path = tmp_path / "not-a-dir"
        file_path.write_text("data")

        with pytest.raises(NotADirectoryError):
            filesystem.SkillProvider.from_directory(file_path)

    def test_from_directory_loads_multiple_skills(self, tmp_path: pathlib.Path) -> None:
        for name in ("rule-creator", "blueprint-creator"):
            skill_dir = tmp_path / "enapter" / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        provider = filesystem.SkillProvider.from_directory(tmp_path)

        assert provider.load_skill("enapter:rule-creator").files[
            pathlib.PurePosixPath("SKILL.md")
        ] == ("# rule-creator")
        assert (
            provider.load_skill("enapter:blueprint-creator").files[
                pathlib.PurePosixPath("SKILL.md")
            ]
            == "# blueprint-creator"
        )

    def test_from_directory_ignores_dirs_without_skill_md(
        self, tmp_path: pathlib.Path
    ) -> None:
        skill_dir = tmp_path / "enapter" / "skills" / "rule-creator"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Index")

        no_skill = tmp_path / "enapter" / "skills" / "not-a-skill"
        no_skill.mkdir(parents=True)

        provider = filesystem.SkillProvider.from_directory(tmp_path)

        with pytest.raises(domain.SkillNotFound):
            provider.load_skill("enapter:not-a-skill")
        provider.load_skill("enapter:rule-creator")

    def test_skill_files_can_be_read(self, tmp_path: pathlib.Path) -> None:
        skill_dir = tmp_path / "enapter" / "skills" / "rule-creator"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Index")

        provider = filesystem.SkillProvider.from_directory(tmp_path)
        skill = provider.load_skill("enapter:rule-creator")

        assert skill.read(pathlib.PurePosixPath("SKILL.md")) == "# Index"

    def test_skill_files_keys_are_posix_paths(self, tmp_path: pathlib.Path) -> None:
        skill_dir = tmp_path / "enapter" / "skills" / "rule-creator"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Index")
        (skill_dir / "deep").mkdir(parents=True)
        (skill_dir / "deep" / "nested.md").write_text("nested")

        provider = filesystem.SkillProvider.from_directory(tmp_path)
        skill = provider.load_skill("enapter:rule-creator")

        assert pathlib.PurePosixPath("deep/nested.md") in skill.files
