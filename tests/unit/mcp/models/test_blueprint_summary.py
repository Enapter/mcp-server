from enapter_mcp_server import domain, mcp


class TestBlueprintSummary:
    """Test cases for BlueprintSummary model."""

    def test_blueprint_summary_from_domain(self) -> None:
        """Test creating BlueprintSummary from domain object."""
        blueprint_summary = domain.BlueprintSummary(
            description="Electrolyzer device",
            vendor="Enapter",
            properties_total=3,
            telemetry_attributes_total=4,
            alerts_total=2,
        )

        summary = mcp.models.BlueprintSummary.from_domain(blueprint_summary)

        assert summary.description == "Electrolyzer device"
        assert summary.vendor == "Enapter"
        assert summary.properties_total == 3
        assert summary.telemetry_attributes_total == 4
        assert summary.alerts_total == 2

    def test_blueprint_summary_from_domain_empty(self) -> None:
        """Test creating BlueprintSummary from empty domain object."""
        blueprint_summary = domain.BlueprintSummary(
            description=None,
            vendor=None,
            properties_total=0,
            telemetry_attributes_total=0,
            alerts_total=0,
        )

        summary = mcp.models.BlueprintSummary.from_domain(blueprint_summary)

        assert summary.description is None
        assert summary.vendor is None
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 0
        assert summary.alerts_total == 0

    def test_blueprint_summary_from_domain_partial(self) -> None:
        """Test creating BlueprintSummary from partial domain object."""
        blueprint_summary = domain.BlueprintSummary(
            description="Partial device",
            vendor=None,
            properties_total=0,
            telemetry_attributes_total=1,
            alerts_total=0,
        )

        summary = mcp.models.BlueprintSummary.from_domain(blueprint_summary)

        assert summary.description == "Partial device"
        assert summary.vendor is None
        assert summary.properties_total == 0
        assert summary.telemetry_attributes_total == 1
        assert summary.alerts_total == 0
