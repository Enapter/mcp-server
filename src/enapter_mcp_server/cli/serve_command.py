import argparse
import asyncio
import os

from enapter_mcp_server import mcp

from .command import Command
from .subparsers import Subparsers

ENAPTER_HTTP_API_URL = os.getenv("ENAPTER_HTTP_API_URL", "https://api.enapter.com")
ENAPTER_LOGO_URL = os.getenv(
    "ENAPTER_LOGO_URL", "https://companieslogo.com/img/orig/H2O.DE-b4a89106.png"
)
ENAPTER_OAUTH_PROXY_ENABLED = os.getenv("ENAPTER_OAUTH_PROXY_ENABLED", "0")
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
ENAPTER_OAUTH_PROXY_ALLOWED_REDIRECT_URLS = os.getenv(
    "ENAPTER_OAUTH_PROXY_ALLOWED_REDIRECT_URLS", ""
)
ENAPTER_OAUTH_PROXY_CLIENT_ID = os.getenv("ENAPTER_OAUTH_PROXY_CLIENT_ID")
ENAPTER_OAUTH_PROXY_CLIENT_SECRET = os.getenv("ENAPTER_OAUTH_PROXY_CLIENT_SECRET")
ENAPTER_OAUTH_PROXY_JWT_STORE_URL = os.getenv(
    "ENAPTER_OAUTH_PROXY_JWT_STORE_URL", "memory://"
)
ENAPTER_OAUTH_PROXY_JWT_SIGNING_KEY = os.getenv("ENAPTER_OAUTH_PROXY_JWT_SIGNING_KEY")


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
            "--logo-url",
            default=ENAPTER_LOGO_URL,
            help="URL of logo to display when connecting to this MCP server",
        )
        parser.add_argument(
            "--oauth-proxy-enabled",
            choices=["0", "1"],
            default=ENAPTER_OAUTH_PROXY_ENABLED,
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
            "--oauth-proxy-allowed-redirect-urls",
            default=ENAPTER_OAUTH_PROXY_ALLOWED_REDIRECT_URLS,
            help="Comma-separated list of allowed redirect URLs for OAuth proxy",
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
        parser.add_argument(
            "--oauth-proxy-jwt-store-url",
            default=ENAPTER_OAUTH_PROXY_JWT_STORE_URL,
            help="URL of JWT store for OAuth proxy (e.g. disk:///tmp/fastmcp)",
        )
        parser.add_argument(
            "--oauth-proxy-jwt-signing-key",
            default=ENAPTER_OAUTH_PROXY_JWT_SIGNING_KEY,
            help="Signing key for JWTs issued by OAuth proxy. Required if OAuth proxy is enabled",
        )

    @staticmethod
    async def run(args: argparse.Namespace) -> None:
        if args.verbose:
            mcp.configure_logging(level="DEBUG")
        host, port_string = args.address.split(":")
        oauth_proxy_config: mcp.OAuthProxyConfig | None = None
        if args.oauth_proxy_enabled == "1":
            required_scopes = [
                scope.strip()
                for scope in args.oauth_proxy_required_scopes.split(",")
                if scope.strip()
            ]
            allowed_redirect_urls = [
                url.strip()
                for url in args.oauth_proxy_allowed_redirect_urls.split(",")
                if url.strip()
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
                allowed_redirect_urls=(
                    allowed_redirect_urls if allowed_redirect_urls else None
                ),
                jwt_store_url=args.oauth_proxy_jwt_store_url,
                jwt_signing_key=args.oauth_proxy_jwt_signing_key,
            )
        config = mcp.ServerConfig(
            host=host,
            port=int(port_string),
            enapter_http_api_url=args.enapter_http_api_url,
            oauth_proxy_config=oauth_proxy_config,
            logo_url=args.logo_url,
        )
        async with asyncio.TaskGroup() as task_group:
            async with mcp.Server(config=config, task_group=task_group):
                await asyncio.Event().wait()
