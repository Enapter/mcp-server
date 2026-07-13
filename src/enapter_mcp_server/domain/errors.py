import pathlib


class UnprefixedRuleSlug(Exception):
    pass


class RuleNotDisabled(Exception):
    pass


class RuleNotMCPManaged(Exception):
    pass


class RuleNotV3(Exception):
    pass


class RuleMustBeCreatedDisabled(Exception):
    pass


class EmptyRuleOldString(Exception):
    pass


class NoOpRuleEdit(Exception):
    pass


class RuleOldStringNotFound(Exception):
    pass


class AmbiguousRuleOldString(Exception):
    pass


class SkillFileNotFound(Exception):
    def __init__(
        self,
        path: pathlib.PurePosixPath,
        valid: list[pathlib.PurePosixPath],
    ) -> None:
        self.path = path
        self.valid = valid
        super().__init__(
            f"Skill file {path!s} not found. Valid files: {[str(p) for p in valid]}"
        )


class SkillNotFound(Exception):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Skill {name!r} not found")
