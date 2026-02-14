from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/orderflow"
    ANTHROPIC_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""


settings = Settings()
