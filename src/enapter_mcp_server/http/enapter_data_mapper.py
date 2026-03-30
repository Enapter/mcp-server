from typing import Any

import enapter

from enapter_mcp_server import core, domain


class EnapterDataMapper:
    def to_device_dto(self, device: Any) -> core.DeviceDTO:
        connectivity = None
        if device.connectivity is not None:
            connectivity = domain.ConnectivityStatus(device.connectivity.status.value)

        return core.DeviceDTO(
            id=device.id,
            name=device.name,
            site_id=device.site_id,
            type=domain.DeviceType(device.type.value),
            connectivity=connectivity,
            properties=device.properties,
            manifest=self.to_device_manifest(device.manifest),
        )

    def to_device_manifest(
        self, manifest: dict[str, Any] | None
    ) -> domain.DeviceManifest | None:
        if manifest is None:
            return None

        return domain.DeviceManifest(
            description=manifest.get("description"),
            vendor=manifest.get("vendor"),
            properties={
                name: self.to_property_declaration(name, dto)
                for name, dto in (manifest.get("properties") or {}).items()
            },
            telemetry={
                name: self.to_telemetry_attribute_declaration(name, dto)
                for name, dto in (manifest.get("telemetry") or {}).items()
            },
            alerts={
                name: self.to_alert_declaration(name, dto)
                for name, dto in (manifest.get("alerts") or {}).items()
            },
            commands={
                name: self.to_command_declaration(name, dto)
                for name, dto in (manifest.get("commands") or {}).items()
            },
        )

    def to_property_declaration(
        self, name: str, dto: dict[str, Any]
    ) -> domain.PropertyDeclaration:
        return domain.PropertyDeclaration(
            name=name,
            display_name=dto["display_name"],
            data_type=domain.DataType(dto["type"]),
            description=dto.get("description"),
            enum=dto.get("enum"),
            unit=dto.get("unit"),
        )

    def to_telemetry_attribute_declaration(
        self, name: str, dto: dict[str, Any]
    ) -> domain.TelemetryAttributeDeclaration:
        return domain.TelemetryAttributeDeclaration(
            name=name,
            display_name=dto["display_name"],
            data_type=domain.DataType(dto["type"]),
            description=dto.get("description"),
            enum=dto.get("enum"),
            unit=dto.get("unit"),
        )

    def to_alert_declaration(
        self, name: str, dto: dict[str, Any]
    ) -> domain.AlertDeclaration:
        return domain.AlertDeclaration(
            name=name,
            display_name=dto["display_name"],
            severity=domain.AlertSeverity(dto["severity"]),
            description=dto.get("description"),
            troubleshooting=dto.get("troubleshooting"),
            components=dto.get("components"),
            conditions=dto.get("conditions"),
        )

    def to_command_declaration(
        self, name: str, dto: dict[str, Any]
    ) -> domain.CommandDeclaration:
        return domain.CommandDeclaration(
            name=name,
            display_name=dto.get("display_name", name),
            description=dto.get("description"),
            arguments=[
                self.to_command_argument_declaration(arg_name, arg_dto)
                for arg_name, arg_dto in (dto.get("arguments") or {}).items()
            ],
        )

    def to_command_argument_declaration(
        self, name: str, dto: dict[str, Any]
    ) -> domain.CommandArgumentDeclaration:
        return domain.CommandArgumentDeclaration(
            name=name,
            display_name=dto.get("display_name", name),
            data_type=domain.DataType(dto["type"]),
            required=dto.get("required", False),
            description=dto.get("description"),
            enum=dto.get("enum"),
        )

    def to_command_execution(
        self, device_id: str, execution: enapter.http.api.commands.Execution
    ) -> domain.CommandExecution:
        return domain.CommandExecution(
            id=execution.id,
            device_id=device_id,
            command_name=execution.request.name,
            state=domain.CommandExecutionState(execution.state.value),
            created_at=execution.created_at,
            arguments=execution.request.arguments,
            response_payload=execution.response.payload if execution.response else None,
        )

    def to_latest_telemetry(
        self,
        telemetry_by_device: dict[
            str, dict[str, enapter.http.api.telemetry.LatestDatapoint | None]
        ],
    ) -> dict[str, dict[str, Any]]:
        return {
            device_id: {
                key: datapoint.value if datapoint is not None else None
                for key, datapoint in device_telemetry.items()
            }
            for device_id, device_telemetry in telemetry_by_device.items()
        }

    def to_historical_telemetry(
        self, telemetry: enapter.http.api.telemetry.WideTimeseries
    ) -> domain.HistoricalTelemetry:
        return domain.HistoricalTelemetry(
            timestamps=telemetry.timestamps,
            values={
                column.labels.telemetry: column.values for column in telemetry.columns
            },
        )
