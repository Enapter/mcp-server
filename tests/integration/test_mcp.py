from enapter_mcp_server import core, http, mcp


class TestServer:

    async def test_ping(self) -> None:
        config = mcp.ServerConfig(
            host="127.0.0.1",
            # FIXME: Hard-code.
            port=12345,
            enapter_http_api_url="",
        )
        async with http.EnapterAPI(base_url=config.enapter_http_api_url) as enapter_api:
            app = core.ApplicationServer(enapter_api=enapter_api)
            async with mcp.Server(app=app, config=config):
                async with mcp.Client(url=f"http://{config.address}/mcp") as client:
                    assert await client.ping()
