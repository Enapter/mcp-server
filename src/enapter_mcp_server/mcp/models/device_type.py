from typing import Literal

DeviceType = Literal[
    "lua",
    "virtual_ucm",
    "hardware_ucm",
    "standalone",
    "gateway",
    "link_master_ucm",
    "link_slave_ucm",
    "embedded_ucm",
    "native",
    "child",
]
