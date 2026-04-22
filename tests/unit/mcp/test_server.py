from unittest.mock import AsyncMock

from enapter_mcp_server.mcp.server import INSTRUCTIONS, Server
from enapter_mcp_server.mcp.server_config import ServerConfig

import mcp.types

def test_register_prompts():
    config = ServerConfig(
        host="127.0.0.1",
        port=12345,
        enapter_http_api_url="https://api.enapter.com",
    )
    app = AsyncMock()
    server = Server(app, config)

    class MockFastMCP:
        def __init__(self):
            self.prompts = {}

        def prompt(self, name, description=None):
            def decorator(func):
                self.prompts[name] = func
                return func
            return decorator

    fastmcp_server = MockFastMCP()
    server._register_prompts(fastmcp_server)

    assert "mcp-server-instructions" in fastmcp_server.prompts
    prompt_func = fastmcp_server.prompts["mcp-server-instructions"]

    messages = prompt_func()
    assert len(messages) == 1

    message = messages[0]
    assert isinstance(message, mcp.types.PromptMessage)
    assert message.role == "user"
    assert message.content.type == "text"
    assert message.content.text == INSTRUCTIONS
