import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class BlueprintSummary:
    description: str | None
    vendor: str | None
    commands_total: int
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int
