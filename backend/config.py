import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_DEFAULT_DB_URL = "postgresql+asyncpg://user:password@localhost:5432/orderflow"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str = _DEFAULT_DB_URL
    ANTHROPIC_API_KEY: str = ""
    WHITE_CIRCLE_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    SAFETY_MODE: str = "log"
    LOG_LEVEL: str = "INFO"


settings = Settings()


def validate_settings() -> None:
    """Run startup validation checks.

    Call once at app init (e.g. from main.py).
    Hard-fails on missing critical config; warns on optional gaps.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # --- Hard failures ---
    if not settings.ANTHROPIC_API_KEY:
        errors.append(
            "[OrderFlow] FATAL: ANTHROPIC_API_KEY is not set.\n"
            "  Set it in your .env file or environment before starting the server."
        )

    if not settings.DATABASE_URL or settings.DATABASE_URL == _DEFAULT_DB_URL:
        errors.append(
            "[OrderFlow] FATAL: DATABASE_URL is not set or still the default placeholder.\n"
            "  Set it in your .env file or environment before starting the server."
        )

    # --- Warnings ---
    if not settings.ELEVENLABS_API_KEY and not settings.OPENAI_API_KEY:
        warnings.append(
            "[OrderFlow] WARNING: Neither ELEVENLABS_API_KEY nor OPENAI_API_KEY is set.\n"
            "  Audio transcription will not work until at least one is configured."
        )

    if not settings.WHITE_CIRCLE_API_KEY and settings.SAFETY_MODE != "off":
        warnings.append(
            "[OrderFlow] WARNING: WHITE_CIRCLE_API_KEY is not set and SAFETY_MODE=%s.\n"
            "  Content safety checks will be skipped until a key is provided."
            % settings.SAFETY_MODE
        )

    for w in warnings:
        logger.warning(w)

    if errors:
        for e in errors:
            logger.critical(e)
        # Also print to stderr so the message is visible even if logging isn't
        # configured yet (e.g. bare `python -c "from config import ..."`)
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
