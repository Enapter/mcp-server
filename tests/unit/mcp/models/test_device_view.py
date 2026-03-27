from enapter_mcp_server import mcp


def test_device_view_literals() -> None:
    basic: mcp.models.DeviceView = "BASIC"
    full: mcp.models.DeviceView = "FULL"
    unspecified: mcp.models.DeviceView = "UNSPECIFIED"

    assert basic == "BASIC"
    assert full == "FULL"
    assert unspecified == "UNSPECIFIED"
