from enapter_mcp_server import mcp


class TestServer:

    async def test_ping(self) -> None:
        host = "127.0.0.1"
        # FIXME: Hard-code.
        port = 12345
        async with mcp.Server(host=host, port=port, enapter_http_api_url=""):
            async with mcp.Client(url=f"http://{host}:{port}/mcp") as client:
                assert await client.ping()
