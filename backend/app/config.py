"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://tendril:tendril@db:5432/tendril"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    google_client_id: str = ""
    google_client_secret: str = ""
    allowed_emails: str = ""  # Comma-separated list
    enable_dev_login: bool = False

    # JWT
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "tendril"

    # Push notifications
    vapid_private_key: str = ""
    vapid_public_key: str = ""

    # App
    app_name: str = "Tendril"
    debug: bool = False
    cors_origins: str = "http://localhost:5173"  # Comma-separated
    base_url: str = ""  # e.g. https://tendril.garden — used to build OAuth redirect URIs

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def allowed_emails_list(self) -> list[str]:
        """Parse comma-separated allowed emails into a list."""
        if not self.allowed_emails:
            return []
        return [email.strip() for email in self.allowed_emails.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
