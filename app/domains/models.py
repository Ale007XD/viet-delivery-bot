from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    """One independent delivery service. slug drives the subdomain
    (slug.nanovm.space) — subdomain is derived, never stored redundantly."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Ho_Chi_Minh")

    # MVP: nullable, single-tenant YooKassa reuses app-level settings.
    # Filled in once per-tenant ShopID model is adopted.
    yookassa_shop_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    yookassa_secret_key: Mapped[str | None] = mapped_column(String(200), nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TenantBot(Base):
    """Independent Telegram bot per tenant (storefront brand decision,
    2026-09-04) — bot_slug is the webhook path segment, token is the
    credential used for setWebhook + sendMessage."""

    __tablename__ = "tenant_bots"
    __table_args__ = (UniqueConstraint("bot_slug", name="uq_tenant_bots_bot_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    bot_slug: Mapped[str] = mapped_column(String(63), nullable=False)
    bot_token: Mapped[str] = mapped_column(String(200), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    customer_telegram_id: Mapped[int] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_amount: Mapped[int] = mapped_column(nullable=False, default=0)  # minor units
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
