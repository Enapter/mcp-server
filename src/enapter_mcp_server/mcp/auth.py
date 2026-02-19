import abc
import urllib.parse

import enapter.http.api
import fastmcp.server.auth
import fastmcp.server.auth.providers.introspection
import fastmcp.server.dependencies
import httpx
import key_value.aio.protocols
import key_value.aio.stores.disk
import key_value.aio.stores.memory

from .oauth_proxy_config import OAuthProxyConfig


class AuthProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def fastmcp_auth_provider(self) -> fastmcp.server.auth.AuthProvider | None:
        pass

    @abc.abstractmethod
    async def get_enapter_auth(self) -> enapter.http.api.Auth:
        pass


class HeaderAuthProvider(AuthProvider):
    @property
    def fastmcp_auth_provider(self) -> fastmcp.server.auth.AuthProvider | None:
        return None

    async def get_enapter_auth(self) -> enapter.http.api.Auth:
        headers = fastmcp.server.dependencies.get_http_headers()
        token = headers.get("x-enapter-auth-token")
        user = headers.get("x-enapter-auth-user")
        return enapter.http.api.Auth(token=token, user=user)


class OAuthProxyAuthProvider(AuthProvider):
    def __init__(self, config: OAuthProxyConfig):
        self._config = config
        self._auth_provider = self._create_auth_provider()

    @property
    def fastmcp_auth_provider(self) -> fastmcp.server.auth.AuthProvider | None:
        return self._auth_provider

    def _create_auth_provider(self) -> fastmcp.server.auth.AuthProvider:
        if self._config.jwt_signing_key is None:
            raise ValueError("jwt_signing_key must be set when oauth_proxy is enabled")

        token_verifier = (
            fastmcp.server.auth.providers.introspection.IntrospectionTokenVerifier(
                introspection_url=self._config.introspection_endpoint_url,
                client_id=self._config.client_id,
                client_secret=self._config.client_secret,
                required_scopes=self._config.required_scopes,
            )
        )
        jwt_store = self._select_jwt_store()
        return fastmcp.server.auth.OAuthProxy(
            upstream_authorization_endpoint=self._config.authorization_endpoint_url,
            upstream_token_endpoint=self._config.token_endpoint_url,
            upstream_client_id=self._config.client_id,
            upstream_client_secret=self._config.client_secret,
            token_verifier=token_verifier,
            base_url=self._config.protected_resource_url,
            forward_pkce=self._config.forward_pkce,
            client_storage=jwt_store,
            jwt_signing_key=self._config.jwt_signing_key,
        )

    def _select_jwt_store(self) -> key_value.aio.protocols.AsyncKeyValue:
        if self._config.jwt_store_url is None:
            return key_value.aio.stores.memory.MemoryStore()
        jwt_store_url = urllib.parse.urlparse(self._config.jwt_store_url)
        match jwt_store_url.scheme:
            case "memory":
                return key_value.aio.stores.memory.MemoryStore()
            case "disk":
                return key_value.aio.stores.disk.DiskStore(directory=jwt_store_url.path)
            case _:
                raise NotImplementedError(f"{jwt_store_url.scheme}")

    async def get_enapter_auth(self) -> enapter.http.api.Auth:
        access_token = fastmcp.server.dependencies.get_access_token()
        assert access_token is not None
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._config.user_info_endpoint_url,
                headers={"Authorization": f"Bearer {access_token.token}"},
            )
            response.raise_for_status()
            user_info = response.json()
            return enapter.http.api.Auth(user=user_info["guid"])
