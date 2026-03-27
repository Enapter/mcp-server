import dataclasses

from .alert_declaration import AlertDeclaration
from .command_declaration import CommandDeclaration
from .property_declaration import PropertyDeclaration
from .telemetry_attribute_declaration import TelemetryAttributeDeclaration


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeviceManifest:
    description: str | None
    vendor: str | None
    properties: dict[str, PropertyDeclaration]
    telemetry: dict[str, TelemetryAttributeDeclaration]
    alerts: dict[str, AlertDeclaration]
    commands: dict[str, CommandDeclaration]
