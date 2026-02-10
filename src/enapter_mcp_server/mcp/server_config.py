import dataclasses

from .oauth_proxy_config import OAuthProxyConfig


@dataclasses.dataclass
class ServerConfig:

    host: str
    port: int
    enapter_http_api_url: str
    oauth_proxy_config: OAuthProxyConfig | None = None

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def oauth_proxy(self) -> OAuthProxyConfig | None:
        return self.oauth_proxy_config
