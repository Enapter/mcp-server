import argparse
import asyncio
import os

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers

ENAPTER_HTTP_API_URL = os.getenv("ENAPTER_HTTP_API_URL", "https://api.enapter.com")
ENAPTER_OAUTH_PROXY_INTROSPECTION_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_INTROSPECTION_URL", "https://sso.enapter.com/oauth/introspect"
)
ENAPTER_OAUTH_PROXY_AUTHORIZATION_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_AUTHORIZATION_URL", "https://sso.enapter.com/oauth/authorize"
)
ENAPTER_OAUTH_PROXY_TOKEN_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_TOKEN_URL", "https://sso.enapter.com/oauth/token"
)
ENAPTER_OAUTH_PROXY_USER_INFO_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_USER_INFO_URL", "https://sso.enapter.com/api/v1/me"
)
ENAPTER_OAUTH_PROXY_PROTECTED_RESOURCE_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_PROTECTED_RESOURCE_URL", "https://mcp.enapter.com"
)
ENAPTER_OAUTH_PROXY_FORWARD_PKCE = os.getenv("ENAPTER_OAUTH_PROXY_FORWARD_PKCE", "1")
ENAPTER_OAUTH_PROXY_REQUIRED_SCOPES = os.getenv(
    "ENAPTER_OAUTH_PROXY_REQUIRED_SCOPES", "openid,public"
)
ENAPTER_OAUTH_PROXY_CLIENT_ID = os.getenv("ENAPTER_OAUTH_PROXY_CLIENT_ID")
ENAPTER_OAUTH_PROXY_CLIENT_SECRET = os.getenv("ENAPTER_OAUTH_PROXY_CLIENT_SECRET")


class ServeCommand(Command):

    @staticmethod
    def register(parent: Subparsers) -> None:
        parser = parent.add_parser(
            "serve", formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            "-u",
            "--enapter-http-api-url",
            default=ENAPTER_HTTP_API_URL,
            help="URL of Enapter HTTP API",
        )
        parser.add_argument(
            "--oauth-proxy-enabled",
            action="store_true",
            help="Enable OAuth proxy for authentication and authorization",
        )
        parser.add_argument(
            "--oauth-proxy-introspection-url",
            default=ENAPTER_OAUTH_PROXY_INTROSPECTION_URL,
            help="Introspection endpoint URL for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-authorization-url",
            default=ENAPTER_OAUTH_PROXY_AUTHORIZATION_URL,
            help="Authorization endpoint URL for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-token-url",
            default=ENAPTER_OAUTH_PROXY_TOKEN_URL,
            help="Token endpoint URL for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-user-info-url",
            default=ENAPTER_OAUTH_PROXY_USER_INFO_URL,
            help="User info endpoint URL for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-protected-resource-url",
            default=ENAPTER_OAUTH_PROXY_PROTECTED_RESOURCE_URL,
            help="URL of protected resource for OAuth proxy (e.g. MCP server URL)",
        )
        parser.add_argument(
            "--oauth-proxy-forward-pkce",
            choices=["0", "1"],
            default=ENAPTER_OAUTH_PROXY_FORWARD_PKCE,
            help="Whether to forward PKCE parameters from authorization request to token request in OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-required-scopes",
            default=ENAPTER_OAUTH_PROXY_REQUIRED_SCOPES,
            help="Comma-separated list of required scopes for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-client-id",
            default=ENAPTER_OAUTH_PROXY_CLIENT_ID,
            help="Client ID for OAuth proxy",
        )
        parser.add_argument(
            "--oauth-proxy-client-secret",
            default=ENAPTER_OAUTH_PROXY_CLIENT_SECRET,
            help="Client secret for OAuth proxy",
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        if args.verbose:
            mcp.configure_logging(level="DEBUG")
        host, port_string = args.address.split(":")
        oauth_proxy_config: mcp.OAuthProxyConfig | None = None
        if args.oauth_proxy_enabled:
            required_scopes = [
                scope.strip()
                for scope in args.oauth_proxy_required_scopes.split(",")
                if scope.strip()
            ]
            oauth_proxy_config = mcp.OAuthProxyConfig(
                introspection_endpoint_url=args.oauth_proxy_introspection_url,
                authorization_endpoint_url=args.oauth_proxy_authorization_url,
                token_endpoint_url=args.oauth_proxy_token_url,
                user_info_endpoint_url=args.oauth_proxy_user_info_url,
                protected_resource_url=args.oauth_proxy_protected_resource_url,
                forward_pkce=args.oauth_proxy_forward_pkce == "1",
                required_scopes=required_scopes,
                client_id=args.oauth_proxy_client_id,
                client_secret=args.oauth_proxy_client_secret,
            )
        config = mcp.ServerConfig(
            host=host,
            port=int(port_string),
            enapter_http_api_url=args.enapter_http_api_url,
            oauth_proxy_config=oauth_proxy_config,
        )
        async with asyncio.TaskGroup() as task_group:
            async with mcp.Server(config=config, task_group=task_group):
                await asyncio.Event().wait()
