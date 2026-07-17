from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "APP_", "env_file": ".env", "extra": "ignore"}

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cloud_atlas"
    )


settings = Settings()
