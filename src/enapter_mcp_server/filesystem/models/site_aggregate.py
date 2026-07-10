import pydantic

from .device import Device
from .site import Site


class SiteAggregate(pydantic.BaseModel):
    site: Site
    devices: list[Device] = []
