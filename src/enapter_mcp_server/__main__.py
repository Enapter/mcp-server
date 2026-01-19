import asyncio

from enapter_mcp_server import cli

app = cli.App.new()
try:
    asyncio.run(app.run())
except KeyboardInterrupt:
    pass
