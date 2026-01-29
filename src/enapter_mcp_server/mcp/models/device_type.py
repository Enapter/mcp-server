import enum


class DeviceType(enum.StrEnum):
    """Enum representing different types of devices.

    Attributes:
        LUA: Device implemented as a Lua script.
        VIRTUAL_UCM: Virtual Universal Communication Module.
        HARDWARE_UCM: Physical Universal Communication Module.
        STANDALONE: Standalone device.
        GATEWAY: Gateway device.
        LINK_MASTER_UCM: Link Master Universal Communication Module.
        LINK_SLAVE_UCM: Link Slave Universal Communication Module.
        EMBEDDED_UCM: Embedded Universal Communication Module.
        NATIVE: Native device.
    """

    LUA = "LUA"
    VIRTUAL_UCM = "VIRTUAL_UCM"
    HARDWARE_UCM = "HARDWARE_UCM"
    STANDALONE = "STANDALONE"
    GATEWAY = "GATEWAY"
    LINK_MASTER_UCM = "LINK_MASTER_UCM"
    LINK_SLAVE_UCM = "LINK_SLAVE_UCM"
    EMBEDDED_UCM = "EMBEDDED_UCM"
    NATIVE = "NATIVE"
