from typing import Protocol

from enapter_mcp_server import domain


class SkillProvider(Protocol):
    def load_skill(self, name: str) -> domain.Skill: ...
