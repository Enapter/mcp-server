from enapter_mcp_server import mcp


def test_device_view_literals() -> None:
    basic: mcp.models.DeviceView = "basic"
    full: mcp.models.DeviceView = "full"

    assert basic == "basic"
    assert full == "full"
