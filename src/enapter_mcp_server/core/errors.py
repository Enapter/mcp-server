class LatestTelemetryUnavailable(Exception):
    pass


class SearchQueryTooBroad(Exception):
    pass


class GatewayUnavailable(Exception):
    pass


class ConfirmationRequired(Exception):
    pass


class CommandNotFound(Exception):
    pass


class UnprefixedRuleSlug(Exception):
    pass


class RuleNotDisabled(Exception):
    pass


class RuleNotMcpManaged(Exception):
    pass


class RuleNotV3(Exception):
    pass


class EmptyRuleOldString(Exception):
    pass


class NoOpRuleEdit(Exception):
    pass


class RuleOldStringNotFound(Exception):
    pass


class AmbiguousRuleOldString(Exception):
    pass
