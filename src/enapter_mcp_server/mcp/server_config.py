import dataclasses


@dataclasses.dataclass
class ServerConfig:

    host: str
    port: int
    enapter_http_api_url: str

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"
