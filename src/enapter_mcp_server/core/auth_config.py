import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class AuthConfig:
    token: str | None = None
    user: str | None = None
