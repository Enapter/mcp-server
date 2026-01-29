import enum


class ConnectivityStatus(enum.StrEnum):
    """Enum representing the connectivity status of a device.

    Connectivity status indicates whether a device is online, offline, or if
    its status is unknown.

    Attributes:
        UNKNOWN: The connectivity status is unknown.
        ONLINE: The device is online.
        OFFLINE: The device is offline.
    """

    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
