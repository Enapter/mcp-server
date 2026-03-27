import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True, kw_only=True)
class BlueprintSummary:
    description: str | None
    vendor: str | None
    commands_total: int
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any]) -> "BlueprintSummary":
        return cls(
            description=manifest.get("description"),
            vendor=manifest.get("vendor"),
            commands_total=len(manifest.get("commands") or {}),
            properties_total=len(manifest.get("properties") or {}),
            telemetry_attributes_total=len(manifest.get("telemetry") or {}),
            alerts_total=len(manifest.get("alerts") or {}),
        )
