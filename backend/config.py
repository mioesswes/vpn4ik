from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    support_chat_id: int | None = Field(default=None, alias="SUPPORT_CHAT_ID")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    xray_shared_uuid: str = Field(alias="XRAY_SHARED_UUID")
    rate_limit_per_minute: int = Field(default=20, alias="RATE_LIMIT_PER_MINUTE")
    trial_duration_days: int = Field(default=0, alias="TRIAL_DURATION_DAYS")

    xray_germany_public_host: str = Field(alias="XRAY_GERMANY_PUBLIC_HOST")
    xray_germany_public_port: int = Field(default=443, alias="XRAY_GERMANY_PUBLIC_PORT")
    xray_germany_reality_public_key: str | None = Field(
        default=None, alias="XRAY_GERMANY_REALITY_PUBLIC_KEY"
    )
    xray_germany_reality_short_id: str | None = Field(
        default=None, alias="XRAY_GERMANY_REALITY_SHORT_ID"
    )
    xray_germany_reality_server_name: str | None = Field(
        default=None, alias="XRAY_GERMANY_REALITY_SERVER_NAME"
    )
    xray_germany_panel_url: str | None = Field(default=None, alias="XRAY_GERMANY_PANEL_URL")
    xray_germany_panel_username: str | None = Field(
        default=None, alias="XRAY_GERMANY_PANEL_USERNAME"
    )
    xray_germany_panel_password: str | None = Field(
        default=None, alias="XRAY_GERMANY_PANEL_PASSWORD"
    )
    xray_germany_inbound_id: str | None = Field(default=None, alias="XRAY_GERMANY_INBOUND_ID")

    xray_sweden_public_host: str = Field(alias="XRAY_SWEDEN_PUBLIC_HOST")
    xray_sweden_public_port: int = Field(default=443, alias="XRAY_SWEDEN_PUBLIC_PORT")
    xray_sweden_reality_public_key: str | None = Field(
        default=None, alias="XRAY_SWEDEN_REALITY_PUBLIC_KEY"
    )
    xray_sweden_reality_short_id: str | None = Field(
        default=None, alias="XRAY_SWEDEN_REALITY_SHORT_ID"
    )
    xray_sweden_reality_server_name: str | None = Field(
        default=None, alias="XRAY_SWEDEN_REALITY_SERVER_NAME"
    )
    xray_sweden_panel_url: str | None = Field(default=None, alias="XRAY_SWEDEN_PANEL_URL")
    xray_sweden_panel_username: str | None = Field(
        default=None, alias="XRAY_SWEDEN_PANEL_USERNAME"
    )
    xray_sweden_panel_password: str | None = Field(
        default=None, alias="XRAY_SWEDEN_PANEL_PASSWORD"
    )
    xray_sweden_inbound_id: str | None = Field(default=None, alias="XRAY_SWEDEN_INBOUND_ID")

    xray_finland_public_host: str = Field(alias="XRAY_FINLAND_PUBLIC_HOST")
    xray_finland_public_port: int = Field(default=443, alias="XRAY_FINLAND_PUBLIC_PORT")
    xray_finland_reality_public_key: str | None = Field(
        default=None, alias="XRAY_FINLAND_REALITY_PUBLIC_KEY"
    )
    xray_finland_reality_short_id: str | None = Field(
        default=None, alias="XRAY_FINLAND_REALITY_SHORT_ID"
    )
    xray_finland_reality_server_name: str | None = Field(
        default=None, alias="XRAY_FINLAND_REALITY_SERVER_NAME"
    )
    xray_finland_panel_url: str | None = Field(default=None, alias="XRAY_FINLAND_PANEL_URL")
    xray_finland_panel_username: str | None = Field(
        default=None, alias="XRAY_FINLAND_PANEL_USERNAME"
    )
    xray_finland_panel_password: str | None = Field(
        default=None, alias="XRAY_FINLAND_PANEL_PASSWORD"
    )
    xray_finland_inbound_id: str | None = Field(default=None, alias="XRAY_FINLAND_INBOUND_ID")

    xray_usa_public_host: str = Field(alias="XRAY_USA_PUBLIC_HOST")
    xray_usa_public_port: int = Field(default=443, alias="XRAY_USA_PUBLIC_PORT")
    xray_usa_reality_public_key: str | None = Field(default=None, alias="XRAY_USA_REALITY_PUBLIC_KEY")
    xray_usa_reality_short_id: str | None = Field(default=None, alias="XRAY_USA_REALITY_SHORT_ID")
    xray_usa_reality_server_name: str | None = Field(
        default=None, alias="XRAY_USA_REALITY_SERVER_NAME"
    )
    xray_usa_panel_url: str | None = Field(default=None, alias="XRAY_USA_PANEL_URL")
    xray_usa_panel_username: str | None = Field(default=None, alias="XRAY_USA_PANEL_USERNAME")
    xray_usa_panel_password: str | None = Field(default=None, alias="XRAY_USA_PANEL_PASSWORD")
    xray_usa_inbound_id: str | None = Field(default=None, alias="XRAY_USA_INBOUND_ID")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: str | int | list[int] | tuple[int, ...] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, tuple):
            return [int(item) for item in value]
        if isinstance(value, list):
            return [int(item) for item in value]
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("support_chat_id", mode="before")
    @classmethod
    def parse_support_chat_id(cls, value: str | int | None) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
