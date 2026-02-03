from enapter_mcp_server.mcp import models


class TestTelemetryAttributeDeclaration:
    """Test cases for TelemetryAttributeDeclaration model."""

    def test_telemetry_attribute_declaration_with_enum(self) -> None:
        """Test creating TelemetryAttributeDeclaration with enum values."""
        attr = models.TelemetryAttributeDeclaration(
            name="status",
            display_name="Status",
            data_type=models.TelemetryAttributeDataType.STRING,
            description="Device status",
            enum=["idle", "running", "error"],
            unit=None,
        )

        assert attr.enum == ["idle", "running", "error"]

    def test_telemetry_attribute_declaration_from_dto(self) -> None:
        """Test creating TelemetryAttributeDeclaration from DTO."""
        dto = {
            "display_name": "Voltage",
            "type": "float",
            "description": "Measured voltage",
            "unit": "V",
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("voltage", dto)

        assert attr.name == "voltage"
        assert attr.display_name == "Voltage"
        assert attr.data_type == models.TelemetryAttributeDataType.FLOAT
        assert attr.description == "Measured voltage"
        assert attr.unit == "V"

    def test_telemetry_attribute_declaration_from_dto_with_enum(self) -> None:
        """Test creating TelemetryAttributeDeclaration from DTO with enum."""
        dto = {
            "display_name": "Operation Mode",
            "type": "string",
            "description": "Current operation mode",
            "enum": ["auto", "manual", "off"],
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("mode", dto)

        assert attr.name == "mode"
        assert attr.display_name == "Operation Mode"
        assert attr.data_type == models.TelemetryAttributeDataType.STRING
        assert attr.description == "Current operation mode"
        assert attr.enum == ["auto", "manual", "off"]
        assert attr.unit is None

    def test_telemetry_attribute_declaration_all_data_types(self) -> None:
        """Test TelemetryAttributeDeclaration with all data types."""
        data_types = [
            models.TelemetryAttributeDataType.INTEGER,
            models.TelemetryAttributeDataType.FLOAT,
            models.TelemetryAttributeDataType.STRING,
            models.TelemetryAttributeDataType.BOOLEAN,
            models.TelemetryAttributeDataType.JSON,
            models.TelemetryAttributeDataType.ARRAY_OF_STRINGS,
            models.TelemetryAttributeDataType.OBJECT,
            models.TelemetryAttributeDataType.ALERTS,
        ]

        for data_type in data_types:
            attr = models.TelemetryAttributeDeclaration(
                name=f"attr_{data_type.value}",
                display_name=f"Attribute {data_type.value}",
                data_type=data_type,
                description=None,
                enum=None,
                unit=None,
            )
            assert attr.data_type == data_type

    def test_telemetry_attribute_declaration_from_dto_minimal(self) -> None:
        """Test creating TelemetryAttributeDeclaration from minimal DTO."""
        dto = {
            "display_name": "Simple Attribute",
            "type": "boolean",
        }

        attr = models.TelemetryAttributeDeclaration.from_dto("simple", dto)

        assert attr.name == "simple"
        assert attr.display_name == "Simple Attribute"
        assert attr.data_type == models.TelemetryAttributeDataType.BOOLEAN
        assert attr.description is None
        assert attr.enum is None
        assert attr.unit is None

    def test_telemetry_attribute_declaration_alerts_type(self) -> None:
        """Test TelemetryAttributeDeclaration with alerts data type."""
        attr = models.TelemetryAttributeDeclaration(
            name="alerts",
            display_name="Active Alerts",
            data_type=models.TelemetryAttributeDataType.ALERTS,
            description="Currently active alerts",
            enum=None,
            unit=None,
        )

        assert attr.data_type == models.TelemetryAttributeDataType.ALERTS
