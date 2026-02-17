from typing import Literal

type DeviceType = Literal[
    "LUA",
    "VIRTUAL_UCM",
    "HARDWARE_UCM",
    "STANDALONE",
    "GATEWAY",
    "LINK_MASTER_UCM",
    "LINK_SLAVE_UCM",
    "EMBEDDED_UCM",
    "NATIVE",
]
