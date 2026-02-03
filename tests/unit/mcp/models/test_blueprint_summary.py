from typing import Any

from enapter_mcp_server.mcp.models.blueprint_summary import BlueprintSummary


class TestBlueprintSummary:
    """Test cases for BlueprintSummary model."""

    def test_blueprint_summary_creation(self) -> None:
        """Test creating BlueprintSummary instance."""
        summary = BlueprintSummary(
            description="Test device",
            vendor="Enapter",
            properties_total=5,
            telemetry_attributes_total=10,
            alerts_total=3,
        )

        assert summary.description == "Test device"
        assert summary.vendor == "Enapter"
        assert summary.properties_total == 5
        assert summary.telemetry_attributes_total == 10
        assert summary.alerts_total == 3

    def test_blueprint_summary_with_none_values(self) -> None:
        """Test creating BlueprintSummary with None values."""
        summary = BlueprintSummary(
            description=None,
            vendor=None,
            properties_total=0,
            telemetry_attributes_total=0,
            alerts_total=0,
        )

        assert summary.description is None
        assert summary.vendor is None
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 0
        assert summary.alerts_total == 0

    def test_blueprint_summary_from_manifest(self) -> None:
        """Test creating BlueprintSummary from manifest."""
        manifest = {
            "description": "Electrolyzer device",
            "vendor": "Enapter",
            "properties": {
                "firmware_version": {"type": "string"},
                "serial_number": {"type": "string"},
                "model": {"type": "string"},
            },
            "telemetry": {
                "temperature": {"type": "float"},
                "pressure": {"type": "float"},
                "voltage": {"type": "float"},
                "current": {"type": "float"},
            },
            "alerts": {
                "high_temperature": {"severity": "warning"},
                "low_pressure": {"severity": "error"},
            },
        }

        summary = BlueprintSummary.from_manifest(manifest)

        assert summary.description == "Electrolyzer device"
        assert summary.vendor == "Enapter"
        assert summary.properties_total == 3
        assert summary.telemetry_attributes_total == 4
        assert summary.alerts_total == 2

    def test_blueprint_summary_from_manifest_empty(self) -> None:
        """Test creating BlueprintSummary from empty manifest."""
        manifest: dict[str, Any] = {}

        summary = BlueprintSummary.from_manifest(manifest)

        assert summary.description is None
        assert summary.vendor is None
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 0
        assert summary.alerts_total == 0

    def test_blueprint_summary_from_manifest_partial(self) -> None:
        """Test creating BlueprintSummary from partial manifest."""
        manifest = {
            "description": "Partial device",
            "telemetry": {
                "temp": {"type": "float"},
            },
        }

        summary = BlueprintSummary.from_manifest(manifest)

        assert summary.description == "Partial device"
        assert summary.vendor is None
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 1
        assert summary.alerts_total == 0
