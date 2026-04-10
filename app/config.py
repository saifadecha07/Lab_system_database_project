from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "healthcheck.railway.app",
    "*.railway.app",
    "*.up.railway.app",
]


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Smart Lab Management System"
    debug: bool = False
    secret_key: str = "change-this-before-production"
    database_url: str
    session_cookie_name: str = "smartlab_session"
    session_max_age: int = 3600
    session_same_site: str = "lax"
    session_https_only: bool = False
    password_hash_scheme: str = "argon2"
    rate_limit_login: str = "5/minute"
    allowed_hosts: list[str] | str = DEFAULT_ALLOWED_HOSTS
    cors_origins: list[str] | str = ["http://localhost:8000"]
    csrf_header_name: str = "X-CSRF-Token"
    csrf_exempt_paths: list[str] | str = ["/auth/login", "/auth/register", "/healthz"]
    penalty_rate_per_hour: int = 25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("allowed_hosts", "cors_origins", "csrf_exempt_paths", mode="before")
    @classmethod
    def split_csv(cls, value: str | list[str]) -> list[str]:
        return _split_csv(value)

    @field_validator("allowed_hosts")
    @classmethod
    def include_platform_hosts(cls, value: list[str]) -> list[str]:
        merged_hosts: list[str] = []
        for host in [*value, *DEFAULT_ALLOWED_HOSTS]:
            if host not in merged_hosts:
                merged_hosts.append(host)
        return merged_hosts

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql+"):
            return value
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    @field_validator("session_same_site")
    @classmethod
    def validate_same_site(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("session_same_site must be one of: lax, strict, none")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
