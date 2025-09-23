from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str  # sync URL for Alembic (psycopg2)
    database_async_url: str | None = None  # async URL for app (asyncpg)
    backend_cors_origins: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()

