from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    # SQLite for quick local development; docker-compose switches this to PostgreSQL.
    database_url: str = "sqlite:///./dev.db"
    codeforces_api_base: str = "https://codeforces.com/api"
    # Codeforces allows roughly 1 request per 2 seconds. Respect it.
    codeforces_min_interval_seconds: float = 2.0
    # Allowed frontend origins for CORS (comma separated).
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
