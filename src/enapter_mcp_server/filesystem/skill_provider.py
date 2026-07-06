import pathlib

from enapter_mcp_server import domain


class SkillProvider:

    def __init__(self, skills: list[domain.Skill] | None = None) -> None:
        self._skills: dict[str, domain.Skill] = {s.name: s for s in (skills or [])}

    @classmethod
    def from_directory(cls, path: pathlib.Path) -> SkillProvider:
        if not path.exists():
            raise FileNotFoundError(f"Skill plugins directory not found: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Skill plugins path is not a directory: {path}")
        skills: list[domain.Skill] = []
        for plugin_dir in sorted(path.iterdir()):
            if not plugin_dir.is_dir():
                continue
            skills.extend(cls._load_plugin(plugin_dir))
        return cls(skills=skills)

    @classmethod
    def _load_plugin(cls, plugin_dir: pathlib.Path) -> list[domain.Skill]:
        skills_root = plugin_dir / "skills"
        if not skills_root.is_dir():
            return []
        skills: list[domain.Skill] = []
        for skill_dir in sorted(skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").is_file():
                continue
            skills.append(
                domain.Skill(
                    name=f"{plugin_dir.name}:{skill_dir.name}",
                    files=cls._load_files(skill_dir),
                )
            )
        return skills

    @staticmethod
    def _load_files(
        skill_dir: pathlib.Path,
    ) -> dict[pathlib.PurePosixPath, str]:
        files: dict[pathlib.PurePosixPath, str] = {}
        for file_path in skill_dir.rglob("*"):
            if not file_path.is_file():
                continue
            relative = pathlib.PurePosixPath(
                file_path.relative_to(skill_dir).as_posix()
            )
            files[relative] = file_path.read_text(encoding="utf-8")
        return files

    def load_skill(self, name: str) -> domain.Skill:
        if name not in self._skills:
            raise domain.SkillNotFound(name)
        return self._skills[name]
