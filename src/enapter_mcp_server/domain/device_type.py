import enum


class DeviceType(enum.Enum):
    LUA = "lua"
    VIRTUAL_UCM = "virtual_ucm"
    HARDWARE_UCM = "hardware_ucm"
    STANDALONE = "standalone"
    GATEWAY = "gateway"
    LINK_MASTER_UCM = "link_master_ucm"
    LINK_SLAVE_UCM = "link_slave_ucm"
    EMBEDDED_UCM = "embedded_ucm"
    NATIVE = "native"
    CHILD = "child"
