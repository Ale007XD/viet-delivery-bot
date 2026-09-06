"""Menu domain: Category, Product.

Two independent axes on Category, both CHECK-constrained, never merged into
one field — this is a lesson imported directly from Sieshka (menu_period
collision, migration 014_menu_period_split, 2026-08-03): a category can be
morning-only AND delivery+pickup, or both-times AND pickup-only — these are
orthogonal, and conflating them into one enum forces categories to lie about
one axis to express the other.

- time_period: when in the day this category is orderable
- fulfillment_scope: which fulfillment methods this category supports

products.time_period_override exists for the same reason as in Sieshka:
a single product can deviate from its category's time window without a
fulfillment override existing at the product level — that axis stays
category-only, mirroring the Sieshka invariant exactly.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domains.models import Base

TIME_PERIODS = ("morning", "evening", "both")
FULFILLMENT_SCOPES = ("delivery", "pickup", "both")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            f"time_period IN {TIME_PERIODS}", name="ck_categories_time_period"
        ),
        CheckConstraint(
            f"fulfillment_scope IN {FULFILLMENT_SCOPES}",
            name="ck_categories_fulfillment_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    time_period: Mapped[str] = mapped_column(String(16), nullable=False, default="both")
    fulfillment_scope: Mapped[str] = mapped_column(String(16), nullable=False, default="both")

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            f"time_period_override IS NULL OR time_period_override IN {TIME_PERIODS}",
            name="ck_products_time_period_override",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # minor units (e.g. VND, no decimals)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # time-of-day axis only — no fulfillment override exists at product level
    # (matches Sieshka invariant exactly, see module docstring)
    time_period_override: Mapped[str | None] = mapped_column(String(16), nullable=True)

    in_stock: Mapped[bool] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
