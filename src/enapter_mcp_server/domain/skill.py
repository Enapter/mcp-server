import dataclasses
import pathlib

from .errors import SkillFileNotFound


@dataclasses.dataclass(frozen=True)
class Skill:
    name: str
    files: dict[pathlib.PurePosixPath, str]

    def read(self, path: pathlib.PurePosixPath) -> str:
        if path not in self.files:
            raise SkillFileNotFound(path, valid=sorted(self.files))
        return self.files[path]
