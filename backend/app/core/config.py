from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    backend_cors_origins: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()

