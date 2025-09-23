from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str  # sync URL for Alembic (psycopg2)
    database_async_url: str | None = None  # async URL for app (asyncpg)
    backend_cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

