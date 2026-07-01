class UnprefixedRuleSlug(Exception):
    pass


class RuleNotDisabled(Exception):
    pass


class RuleNotMcpManaged(Exception):
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
