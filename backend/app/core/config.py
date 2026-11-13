"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BETPREDICT AI"
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "dev-secret-change-me"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    demo_mode: bool = True

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    legal_age_minimum: int = 18

    database_url: str = "postgresql+asyncpg://betpredict:betpredict_secret@localhost:5432/betpredict"
    database_url_sync: str = "postgresql://betpredict:betpredict_secret@localhost:5432/betpredict"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    sportmonks_token: str = ""
    sportmonks_base_url: str = "https://api.sportmonks.com/v3/football"
    football_data_org_key: str = ""
    football_data_org_base_url: str = "https://api.football-data.org/v4"
    primary_data_provider: str = "demo"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_premium: str = ""
    stripe_price_pro: str = ""

    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "betpredict-football"

    free_daily_analyses: int = 5
    premium_daily_analyses: int = 100
    pro_daily_analyses: int = 10_000

    @field_validator("demo_mode", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_demo(self) -> bool:
        """Demo mode when explicitly set or when no licensed provider key is configured."""
        if self.demo_mode:
            return True
        provider = self.primary_data_provider.lower()
        if provider == "demo":
            return True
        if provider == "api_football" and not self.api_football_key:
            return True
        if provider == "sportmonks" and not self.sportmonks_token:
            return True
        if provider == "football_data_org" and not self.football_data_org_key:
            return True
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
