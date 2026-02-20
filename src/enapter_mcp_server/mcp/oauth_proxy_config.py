import dataclasses


@dataclasses.dataclass
class OAuthProxyConfig:

    introspection_endpoint_url: str
    authorization_endpoint_url: str
    token_endpoint_url: str
    user_info_endpoint_url: str
    protected_resource_url: str
    forward_pkce: bool
    required_scopes: list[str]
    client_id: str
    client_secret: str
    allowed_redirect_urls: list[str] | None = None
    jwt_store_url: str | None = None
    jwt_signing_key: str | None = None
