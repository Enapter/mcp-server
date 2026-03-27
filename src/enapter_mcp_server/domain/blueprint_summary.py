import dataclasses

from .device_manifest import DeviceManifest


@dataclasses.dataclass(frozen=True, kw_only=True)
class BlueprintSummary:
    description: str | None
    vendor: str | None
    commands_total: int
    properties_total: int
    telemetry_attributes_total: int
    alerts_total: int

    @classmethod
    def from_device_manifest(cls, manifest: DeviceManifest) -> "BlueprintSummary":
        return cls(
            description=manifest.description,
            vendor=manifest.vendor,
            commands_total=len(manifest.commands),
            properties_total=len(manifest.properties),
            telemetry_attributes_total=len(manifest.telemetry),
            alerts_total=len(manifest.alerts),
        )
