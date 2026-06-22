from enapter_mcp_server import domain


class TestBlueprintSummary:
    def test_from_device_manifest(self) -> None:
        manifest = domain.DeviceManifest(
            description="Electrolyzer device",
            vendor="Enapter",
            implements=[],
            commands={
                "c1": domain.CommandDeclaration(
                    name="c1",
                    display_name="C1",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                ),
                "c2": domain.CommandDeclaration(
                    name="c2",
                    display_name="C2",
                    access_level=domain.AccessRole.USER,
                    description=None,
                    arguments=[],
                    implements=[],
                ),
            },
            properties={
                "p1": domain.PropertyDeclaration(
                    name="p1",
                    display_name="P1",
                    data_type=domain.DataType.STRING,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                )
            },
            telemetry={
                "t1": domain.TelemetryAttributeDeclaration(
                    name="t1",
                    display_name="T1",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                ),
                "t2": domain.TelemetryAttributeDeclaration(
                    name="t2",
                    display_name="T2",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                ),
                "t3": domain.TelemetryAttributeDeclaration(
                    name="t3",
                    display_name="T3",
                    data_type=domain.DataType.FLOAT,
                    access_level=domain.AccessRole.READONLY,
                    description=None,
                    enum=None,
                    unit=None,
                    implements=[],
                ),
            },
            alerts={
                "a1": domain.AlertDeclaration(
                    name="a1",
                    display_name="A1",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                ),
                "a2": domain.AlertDeclaration(
                    name="a2",
                    display_name="A2",
                    severity=domain.AlertSeverity.WARNING,
                    description=None,
                    troubleshooting=None,
                    components=None,
                    conditions=None,
                ),
            },
        )

        summary = domain.BlueprintSummary.from_device_manifest(manifest)

        assert summary.description == "Electrolyzer device"
        assert summary.vendor == "Enapter"
        assert summary.commands_total == 2
        assert summary.properties_total == 1
        assert summary.telemetry_attributes_total == 3
        assert summary.alerts_total == 2

    def test_from_device_manifest_missing_sections(self) -> None:
        summary = domain.BlueprintSummary.from_device_manifest(
            domain.DeviceManifest(
                description=None,
                vendor=None,
                implements=[],
                commands={},
                properties={},
                telemetry={},
                alerts={},
            )
        )

        assert summary.description is None
        assert summary.vendor is None
        assert summary.commands_total == 0
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 0
        assert summary.alerts_total == 0
