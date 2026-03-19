import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class BlueprintSummary:
    description: str | None
    vendor: str | None
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int
