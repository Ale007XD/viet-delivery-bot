from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    ROOT_DOMAIN: str = "nanovm.space"

    # YooKassa — one ShopID for now (MVP single-tenant decision, 2026-09-04).
    # Multi-ShopID-per-tenant model deferred; schema already carries
    # tenants.yookassa_shop_id nullable so it's not a breaking migration later.
    YOOKASSA_SHOP_ID: str | None = None
    YOOKASSA_SECRET_KEY: str | None = None

    TELEGRAM_WEBHOOK_SECRET: str = "change-me"  # sent as X-Telegram-Bot-Api-Secret-Token


settings = Settings()  # type: ignore[call-arg]
