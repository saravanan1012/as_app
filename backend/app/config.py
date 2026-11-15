from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "as_app"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+psycopg2://as:as_dev@localhost:5433/as_app"

    auth_secret: str = "change-me-phase1-dev-secret-min-32-chars!!"
    auth_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cookie_name: str = "as_session"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    auth_url: str = "http://localhost:8000"

    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    default_vendor_id: int = 1
    storage_root: str = "./storage"

    # Razorpay — mock=true skips live API (local/CI). Set mock=false + keys for real payments.
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_mock: bool = True

    # SMTP — empty host/password disables outbound mail (tests/local without credentials).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    # Comma-separated recipients for new-order packing alerts (defaults to smtp_user).
    order_notify_to: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def order_notify_recipients(self) -> list[str]:
        raw = self.order_notify_to or self.smtp_user
        return [e.strip() for e in raw.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
