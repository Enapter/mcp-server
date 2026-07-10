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


class RuleNotFound(Exception):
    def __init__(self, rule_id: str, site_id: str) -> None:
        self.rule_id = rule_id
        self.site_id = site_id
        super().__init__(f"Rule {rule_id!r} not found on site {site_id!r}")


class DeviceNotFound(Exception):
    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Device {device_id!r} not found")


class SiteNotFound(Exception):
    def __init__(self, site_id: str) -> None:
        self.site_id = site_id
        super().__init__(f"Site {site_id!r} not found")


class RuleEngineNotFound(Exception):
    def __init__(self, site_id: str) -> None:
        self.site_id = site_id
        super().__init__(f"Rule engine for site {site_id!r} not found")


class RuleSlugConflict(Exception):
    def __init__(self, slug: str, site_id: str) -> None:
        self.slug = slug
        self.site_id = site_id
        super().__init__(f"Rule with slug {slug!r} already exists on site {site_id!r}")
