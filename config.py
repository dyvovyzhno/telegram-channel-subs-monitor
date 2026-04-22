"""Runtime configuration.

All env-backed settings live on a single `Settings` instance. Importing
`settings` from anywhere triggers validation: missing or empty values
fail fast at startup with a descriptive pydantic error instead of a
generic `ValueError` deep in a module.

.env is loaded automatically (compatible with the existing layout).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram API (my.telegram.org)
    API_ID: int = Field(gt=0)
    API_HASH: str = Field(min_length=1)
    PHONE_NUMBER: str = Field(min_length=1)

    # Source channel we monitor
    CHANNEL_ID_TO_MONITOR: str = Field(min_length=1)
    # Invite link used to re-verify delivery on the receiver side
    CHAT_URL: str = Field(min_length=1)

    # Notification bot (BotFather) and its target chat
    BOT_API: str = Field(min_length=1)
    CHAT_ID: str = Field(min_length=1)

    # Sentry DSN (required; the pipeline relies on it for error visibility)
    SENTRY_DSN: str = Field(min_length=1)

    # Logging verbosity — raise to "DEBUG" when investigating, lower to "WARNING" for quieter prod
    LOG_LEVEL: str = "INFO"

    # Absolute path to the Firebase service-account JSON. Optional: when unset we fall
    # back to "serviceAccountKey.json" in the working dir so existing deployments keep
    # working. Prefer an absolute path outside the repo (e.g. /etc/secrets/…) so the
    # key lives outside version-controlled territory.
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None


settings = Settings()  # type: ignore[call-arg]
