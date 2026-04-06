import os

from pydantic import Field
from pydantic_settings import BaseSettings


def _read_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip()
    return normalized if normalized else default


def _read_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


def _build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    return (
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'user')}:{os.getenv('POSTGRES_PASSWORD', 'password')}"
        f"@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'smsdb')}"
    )


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default=_read_env("ENVIRONMENT", "development"))
    DATABASE_URL: str = Field(default_factory=_build_database_url)
    CLASSIFICATION_URL: str = Field(default=_read_env("CLASSIFICATION_URL", "http://classification-service:8080"))
    SECRET_KEY: str = Field(default=_read_env("SECRET_KEY", "change-in-production"))
    ENFORCE_API_KEY: bool = Field(default=_read_bool_env("ENFORCE_API_KEY", True))
    ADMIN_API_KEY: str = Field(default=_read_env("ADMIN_API_KEY", "change-admin-in-production"))
    INTERNAL_SERVICE_TOKEN: str = Field(default=_read_env("INTERNAL_SERVICE_TOKEN", "change-service-token-in-production"))
    HYBRID_LLM_THRESHOLD: float = Field(default=float(_read_env("HYBRID_LLM_THRESHOLD", "0.7")))
    CORS_ORIGINS: str = Field(default=_read_env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))
    ALLOWED_HOSTS: str = Field(default=_read_env("ALLOWED_HOSTS", "localhost,127.0.0.1,gateway-service"))
    GATEWAY_RATE_LIMIT_PER_MINUTE: int = Field(default=int(_read_env("GATEWAY_RATE_LIMIT_PER_MINUTE", "120")))
    GATEWAY_ADMIN_RATE_LIMIT_PER_MINUTE: int = Field(default=int(_read_env("GATEWAY_ADMIN_RATE_LIMIT_PER_MINUTE", "20")))

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"prod", "production"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    def validate_runtime_security(self) -> list[str]:
        if not self.is_production:
            return []

        issues: list[str] = []
        insecure_secret_values = {"change-in-production", "change-me"}
        insecure_admin_values = {"change-admin-in-production", "change-admin-key"}
        insecure_internal_values = {"change-service-token-in-production", "change-me", "internal-token"}

        if not self.ENFORCE_API_KEY:
            issues.append("ENFORCE_API_KEY must remain enabled in production.")
        if self.SECRET_KEY in insecure_secret_values:
            issues.append("SECRET_KEY is using an insecure default value.")
        if self.ADMIN_API_KEY in insecure_admin_values:
            issues.append("ADMIN_API_KEY is using an insecure default value.")
        if self.INTERNAL_SERVICE_TOKEN in insecure_internal_values:
            issues.append("INTERNAL_SERVICE_TOKEN is using an insecure default value.")
        if self.ADMIN_API_KEY == self.SECRET_KEY:
            issues.append("ADMIN_API_KEY must not reuse SECRET_KEY.")
        if "*" in self.allowed_host_list:
            issues.append("ALLOWED_HOSTS must not contain '*' in production.")

        return issues


settings = Settings()
