from enapter_mcp_server.mcp.models.property_data_type import PropertyDataType
from enapter_mcp_server.mcp.models.property_declaration import PropertyDeclaration


class TestPropertyDeclaration:
    """Test cases for PropertyDeclaration model."""

    def test_property_declaration_creation(self) -> None:
        """Test creating PropertyDeclaration instance."""
        prop = PropertyDeclaration(
            name="firmware_version",
            display_name="Firmware Version",
            data_type=PropertyDataType.STRING,
            description="Current firmware version",
            enum=None,
            unit=None,
        )

        assert prop.name == "firmware_version"
        assert prop.display_name == "Firmware Version"
        assert prop.data_type == PropertyDataType.STRING
        assert prop.description == "Current firmware version"
        assert prop.enum is None
        assert prop.unit is None

    def test_property_declaration_with_enum(self) -> None:
        """Test creating PropertyDeclaration with enum values."""
        prop = PropertyDeclaration(
            name="mode",
            display_name="Operation Mode",
            data_type=PropertyDataType.STRING,
            description="Current operation mode",
            enum=["auto", "manual", "standby"],
            unit=None,
        )

        assert prop.enum == ["auto", "manual", "standby"]

    def test_property_declaration_with_unit(self) -> None:
        """Test creating PropertyDeclaration with unit."""
        prop = PropertyDeclaration(
            name="max_temperature",
            display_name="Maximum Temperature",
            data_type=PropertyDataType.FLOAT,
            description="Maximum operating temperature",
            enum=None,
            unit="°C",
        )

        assert prop.unit == "°C"
        assert prop.data_type == PropertyDataType.FLOAT

    def test_property_declaration_from_dto(self) -> None:
        """Test creating PropertyDeclaration from DTO."""
        dto = {
            "display_name": "Serial Number",
            "type": "string",
            "description": "Device serial number",
        }

        prop = PropertyDeclaration.from_dto("serial_number", dto)

        assert prop.name == "serial_number"
        assert prop.display_name == "Serial Number"
        assert prop.data_type == PropertyDataType.STRING
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

        prop = PropertyDeclaration.from_dto("status", dto)

        assert prop.name == "status"
        assert prop.display_name == "Status"
        assert prop.data_type == PropertyDataType.STRING
        assert prop.description == "Device status"
        assert prop.enum == ["active", "inactive", "error"]
        assert prop.unit == "state"

    def test_property_declaration_all_data_types(self) -> None:
        """Test PropertyDeclaration with all data types."""
        data_types = [
            PropertyDataType.INTEGER,
            PropertyDataType.FLOAT,
            PropertyDataType.STRING,
            PropertyDataType.BOOLEAN,
            PropertyDataType.JSON,
            PropertyDataType.ARRAY_OF_STRINGS,
            PropertyDataType.OBJECT,
        ]

        for data_type in data_types:
            prop = PropertyDeclaration(
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

        prop = PropertyDeclaration.from_dto("simple", dto)

        assert prop.name == "simple"
        assert prop.display_name == "Simple Property"
        assert prop.data_type == PropertyDataType.INTEGER
        assert prop.description is None
        assert prop.enum is None
        assert prop.unit is None
