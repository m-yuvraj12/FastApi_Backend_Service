from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/notifications"

    # JWT
    secret_key: str  # required - no default on purpose
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Firebase Cloud Messaging
    firebase_credentials_path: str = "secrets/firebase-service-account.json"
    # When true, FCM validates the message but does NOT deliver it (useful for CI).
    fcm_dry_run: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
