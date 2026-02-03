from enapter_mcp_server.mcp import models


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_with_enum(self) -> None:
        """Test creating PropertyDeclaration with enum values."""
        prop = models.PropertyDeclaration(
            name="mode",
            display_name="Operation Mode",
            data_type=models.PropertyDataType.STRING,
            description="Current operation mode",
            enum=["auto", "manual", "standby"],
            unit=None,
        )

        assert prop.enum == ["auto", "manual", "standby"]

    def test_property_declaration_with_unit(self) -> None:
        """Test creating PropertyDeclaration with unit."""
        prop = models.PropertyDeclaration(
            name="max_temperature",
            display_name="Maximum Temperature",
            data_type=models.PropertyDataType.FLOAT,
            description="Maximum operating temperature",
            enum=None,
            unit="°C",
        )

        assert prop.unit == "°C"
        assert prop.data_type == models.PropertyDataType.FLOAT

    def test_property_declaration_from_dto(self) -> None:
        """Test creating PropertyDeclaration from DTO."""
        dto = {
            "display_name": "Serial Number",
            "type": "string",
            "description": "Device serial number",
        }

        prop = models.PropertyDeclaration.from_dto("serial_number", dto)

        assert prop.name == "serial_number"
        assert prop.display_name == "Serial Number"
        assert prop.data_type == models.PropertyDataType.STRING
        assert prop.description == "Device serial number"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_from_dto_with_enum_and_unit(self) -> None:
        """Test creating PropertyDeclaration from DTO with enum and unit."""
        dto = {
            "display_name": "Status",
            "type": "string",
            "description": "Device status",
            "enum": ["active", "inactive", "error"],
            "unit": "state",
        }

        prop = models.PropertyDeclaration.from_dto("status", dto)

        assert prop.name == "status"
        assert prop.display_name == "Status"
        assert prop.data_type == models.PropertyDataType.STRING
        assert prop.description == "Device status"
        assert prop.enum == ["active", "inactive", "error"]
        assert prop.unit == "state"

    def test_property_declaration_all_data_types(self) -> None:
        """Test PropertyDeclaration with all data types."""
        data_types = [
            models.PropertyDataType.INTEGER,
            models.PropertyDataType.FLOAT,
            models.PropertyDataType.STRING,
            models.PropertyDataType.BOOLEAN,
            models.PropertyDataType.JSON,
            models.PropertyDataType.ARRAY_OF_STRINGS,
            models.PropertyDataType.OBJECT,
        ]

        for data_type in data_types:
            prop = models.PropertyDeclaration(
                name=f"prop_{data_type.value}",
                display_name=f"Property {data_type.value}",
                data_type=data_type,
                description=None,
                enum=None,
                unit=None,
            )
            assert prop.data_type == data_type

    def test_property_declaration_from_dto_minimal(self) -> None:
        """Test creating PropertyDeclaration from minimal DTO."""
        dto = {
            "display_name": "Simple Property",
            "type": "integer",
        }

        prop = models.PropertyDeclaration.from_dto("simple", dto)

        assert prop.name == "simple"
        assert prop.display_name == "Simple Property"
        assert prop.data_type == models.PropertyDataType.INTEGER
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None
