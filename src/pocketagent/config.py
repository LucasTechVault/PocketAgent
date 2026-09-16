"""Application configuration for the bootstrap milestone."""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load defaults, then a local .env file, then environment overrides."""

    model_config = SettingsConfigDict(
        env_prefix="POCKETAGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", min_length=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        """Accept conventional logging levels regardless of letter case."""
        if isinstance(value, str):
            return value.upper()
        return value
