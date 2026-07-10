import pydantic

from .rule import Rule
from .rule_engine import RuleEngine


class RuleEngineAggregate(pydantic.BaseModel):
    rule_engine: RuleEngine
    rules: list[Rule] = []
