from enapter_mcp_server import domain


class TestBlueprintSummary:
    def test_from_manifest(self) -> None:
        manifest = {
            "description": "Electrolyzer device",
            "vendor": "Enapter",
            "commands": {"c1": {}, "c2": {}},
            "properties": {"p1": {}},
            "telemetry": {"t1": {}, "t2": {}, "t3": {}},
            "alerts": {"a1": {}, "a2": {}},
        }

        summary = domain.BlueprintSummary.from_manifest(manifest)

        assert summary.description == "Electrolyzer device"
        assert summary.vendor == "Enapter"
        assert summary.commands_total == 2
        assert summary.properties_total == 1
        assert summary.telemetry_attributes_total == 3
        assert summary.alerts_total == 2

    def test_from_manifest_missing_sections(self) -> None:
        summary = domain.BlueprintSummary.from_manifest({})

        assert summary.description is None
        assert summary.vendor is None
        assert summary.commands_total == 0
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 0
        assert summary.alerts_total == 0
