from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    FRONTEND_URL: str
    SESSION_SECRET_KEY: str

    DELHIVERY_API_KEY: str = ""
    DELHIVERY_BASE_URL: str = "https://track.delhivery.com/api"

    CORS_ORIGINS: str = "*"

    # Debug flag: bypass the DB pool size cap (uses NullPool - unlimited connections)
    # to test whether pool contention is actually the bottleneck. Not meant to stay on.
    DB_POOL_UNLIMITED: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return self.CORS_ORIGINS.split(",")


settings = Settings()
