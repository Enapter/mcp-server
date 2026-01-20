import datetime
import enum
from typing import Any, Self

import enapter
import pydantic


class Site(pydantic.BaseModel):

    id: str
    name: str
    timezone: str

    @classmethod
    def from_domain(cls, site: enapter.http.api.sites.Site) -> Self:
        return cls(id=site.id, name=site.name, timezone=site.timezone)


class DeviceType(enum.StrEnum):

    LUA = "LUA"
    VIRTUAL_UCM = "VIRTUAL_UCM"
    HARDWARE_UCM = "HARDWARE_UCM"
    STANDALONE = "STANDALONE"
    GATEWAY = "GATEWAY"
    LINK_MASTER_UCM = "LINK_MASTER_UCM"
    LINK_SLAVE_UCM = "LINK_SLAVE_UCM"
    EMBEDDED_UCM = "EMBEDDED_UCM"
    NATIVE = "NATIVE"


class DeviceConnectivityStatus(enum.StrEnum):

    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class Device(pydantic.BaseModel):

    id: str
    blueprint_id: str
    name: str
    site_id: str
    type: DeviceType

    @classmethod
    def from_domain(cls, device: enapter.http.api.devices.Device) -> Self:
        return cls(
            id=device.id,
            blueprint_id=device.blueprint_id,
            name=device.name,
            site_id=device.site_id,
            type=DeviceType(device.type.value),
        )


class HistoricalTelemetryData(pydantic.BaseModel):

    timestamps: list[datetime.datetime]
    values: dict[str, list[Any]]
