from typing import Any, Self

import fastmcp


class Client:

    def __init__(
        self,
        url: str,
        enapter_auth_token: str | None = None,
        enapter_auth_user: str | None = None,
    ) -> None:
        self._client = self._new_client(url, enapter_auth_token, enapter_auth_user)

    def _new_client(
        self, url: str, enapter_auth_token: str | None, enapter_auth_user: str | None
    ) -> fastmcp.Client:
        headers = {}
        if enapter_auth_token is not None:
            headers["x-enapter-auth-token"] = enapter_auth_token
        if enapter_auth_user is not None:
            headers["x-enapter-auth-user"] = enapter_auth_user
        transport = fastmcp.client.StreamableHttpTransport(url, headers=headers)
        return fastmcp.Client(transport=transport)

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.__aexit__(*exc)

    async def ping(self) -> bool:
        return await self._client.ping()

    async def list_tools(self) -> Any:
        return await self._client.list_tools()

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        return await self._client.call_tool(name, arguments)
