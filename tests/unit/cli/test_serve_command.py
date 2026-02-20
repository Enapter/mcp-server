import argparse
import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from enapter_mcp_server.cli.serve_command import ServeCommand
from enapter_mcp_server import mcp

class TestServeCommand:
    @pytest.mark.asyncio
    async def test_run_parses_allowed_redirect_urls(self):
        args = argparse.Namespace(
            address="127.0.0.1:8080",
            enapter_http_api_url="https://api.example.com",
            logo_url="https://logo.example.com",
            oauth_proxy_enabled="1",
            oauth_proxy_introspection_url="https://sso.example.com/introspect",
            oauth_proxy_authorization_url="https://sso.example.com/authorize",
            oauth_proxy_token_url="https://sso.example.com/token",
            oauth_proxy_user_info_url="https://sso.example.com/me",
            oauth_proxy_protected_resource_url="https://mcp.example.com",
            oauth_proxy_forward_pkce="1",
            oauth_proxy_required_scopes="openid,profile",
            oauth_proxy_allowed_redirect_urls="http://localhost:3000,http://localhost:3001",
            oauth_proxy_client_id="client_id",
            oauth_proxy_client_secret="client_secret",
            oauth_proxy_jwt_store_url="memory://",
            oauth_proxy_jwt_signing_key="signing_key",
            verbose=False
        )

        with patch("enapter_mcp_server.mcp.Server", autospec=True) as mock_server:
            # We need to mock the async context manager
            mock_server_instance = mock_server.return_value
            mock_server_instance.__aenter__.return_value = mock_server_instance

            # ServeCommand.run has an infinite wait, so we need to break it
            with patch("asyncio.Event.wait", side_effect=asyncio.CancelledError):
                with pytest.raises(asyncio.CancelledError):
                    await ServeCommand.run(args)

            mock_server.assert_called_once()
            config = mock_server.call_args[1]["config"]
            assert config.oauth_proxy is not None
            assert config.oauth_proxy.allowed_redirect_urls == ["http://localhost:3000", "http://localhost:3001"]

    @pytest.mark.asyncio
    async def test_run_handles_empty_allowed_redirect_urls(self):
        args = argparse.Namespace(
            address="127.0.0.1:8080",
            enapter_http_api_url="https://api.example.com",
            logo_url="https://logo.example.com",
            oauth_proxy_enabled="1",
            oauth_proxy_introspection_url="https://sso.example.com/introspect",
            oauth_proxy_authorization_url="https://sso.example.com/authorize",
            oauth_proxy_token_url="https://sso.example.com/token",
            oauth_proxy_user_info_url="https://sso.example.com/me",
            oauth_proxy_protected_resource_url="https://mcp.example.com",
            oauth_proxy_forward_pkce="1",
            oauth_proxy_required_scopes="openid,profile",
            oauth_proxy_allowed_redirect_urls="",
            oauth_proxy_client_id="client_id",
            oauth_proxy_client_secret="client_secret",
            oauth_proxy_jwt_store_url="memory://",
            oauth_proxy_jwt_signing_key="signing_key",
            verbose=False
        )

        with patch("enapter_mcp_server.mcp.Server", autospec=True) as mock_server:
            mock_server_instance = mock_server.return_value
            mock_server_instance.__aenter__.return_value = mock_server_instance

            with patch("asyncio.Event.wait", side_effect=asyncio.CancelledError):
                with pytest.raises(asyncio.CancelledError):
                    await ServeCommand.run(args)

            config = mock_server.call_args[1]["config"]
            assert config.oauth_proxy.allowed_redirect_urls is None
