import pytest

from enapter_mcp_server import fake, http
from enapter_mcp_server.cli import serve_command


class TestMakeEnapterAPI:
    def test_fake_url_creates_fake_adapter(self) -> None:
        api = serve_command._make_enapter_api(
            "fake://?state=tests.unit.fake._sample_state"
        )
        assert isinstance(api, fake.EnapterAPI)

    def test_filetree_url_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            serve_command._make_enapter_api("filetree:///tmp/state")

    def test_https_url_creates_http_adapter(self) -> None:
        api = serve_command._make_enapter_api("https://api.enapter.com")
        assert isinstance(api, http.EnapterAPI)

    def test_http_url_creates_http_adapter(self) -> None:
        api = serve_command._make_enapter_api("http://localhost:8080")
        assert isinstance(api, http.EnapterAPI)

    def test_unsupported_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            serve_command._make_enapter_api("ftp://example.com/state")

    def test_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            serve_command._make_enapter_api("")
