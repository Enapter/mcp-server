import contextlib
from typing import AsyncGenerator, cast

import enapter

from enapter_mcp_server import core, http


class FailingTelemetryClient:
    async def latest(
        self, attributes_by_device: dict[str, list[str]]
    ) -> dict[str, dict[str, enapter.http.api.telemetry.LatestDatapoint | None]]:
        raise enapter.http.api.Error(
            message="broken device",
            code="bad_device",
            details={"device_id": "dev-1"},
        )


class FakeClient:
    def __init__(self) -> None:
        self.telemetry = FailingTelemetryClient()


class StubEnapterAPI(http.EnapterAPI):
    @contextlib.asynccontextmanager
    async def _new_client(
        self, auth: core.AuthConfig
    ) -> AsyncGenerator[enapter.http.api.Client, None]:
        yield cast(enapter.http.api.Client, FakeClient())


class TestEnapterAPI:
    async def test_get_latest_telemetry_raises_latest_telemetry_unavailable(
        self,
    ) -> None:
        api = StubEnapterAPI(base_url="http://example.test")

        try:
            await api.get_latest_telemetry(
                core.AuthConfig(token="test"),
                {"dev-1": ["alerts"]},
            )
        except core.LatestTelemetryUnavailable:
            pass
        else:
            raise AssertionError("Expected LatestTelemetryUnavailable")
