"""MenuService.

Lesson imported from Sieshka (menu_period-collision-session, 2026-08-03):
MenuService.get_menu(method) accepted `method` but never used it in the SQL
WHERE clause — a silent no-op filter shipped and went unnoticed until an
explicit audit. The fix here is to write the filter into the query from the
start and cover it with a test that would fail if the parameter were ever
dropped from the WHERE clause again (test_menu_service.py).

time_period filtering: category/product ordering windows are evaluated
against the tenant's own timezone (tenants.timezone), never the VPS's
system clock (Sieshka invariant: never bind 'today'/time comparisons to
server-local time — VPS and business timezone routinely diverge).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.menu import Category, Product
from app.domains.models import Tenant

# Category.time_period == "morning" is orderable [00:00, MORNING_END_HOUR);
# "evening" is orderable [MORNING_END_HOUR, 24:00). "both" always orderable.
# A single flat cutoff is an MVP simplification — real per-tenant business
# hours (open/close, not just AM/PM split) is a separate, larger feature
# (see Sieshka's own ScheduleWindow / operating-hours-cost-session for the
# scope of doing this properly) and explicitly deferred, not silently
# conflated with this field.
MORNING_END_HOUR = 15


def _current_period(tenant_tz: str) -> str:
    now = datetime.now(ZoneInfo(tenant_tz))
    return "morning" if now.hour < MORNING_END_HOUR else "evening"


class MenuService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_menu(self, *, tenant_id: str, method: str) -> list[dict]:
        """method: 'delivery' | 'pickup'. Returns categories with nested
        active, in-scope products, ordered by Category.sort/Product.sort."""
        if method not in ("delivery", "pickup"):
            raise ValueError(f"unknown fulfillment method: {method!r}")

        tenant = await self._session.get(Tenant, uuid.UUID(tenant_id))
        if tenant is None:
            raise ValueError(f"tenant {tenant_id} not found")

        period = _current_period(tenant.timezone)

        cat_result = await self._session.execute(
            select(Category)
            .where(
                Category.tenant_id == uuid.UUID(tenant_id),
                Category.is_active.is_(True),
                or_(Category.fulfillment_scope == "both", Category.fulfillment_scope == method),
                or_(Category.time_period == "both", Category.time_period == period),
            )
            .order_by(Category.sort)
        )
        categories = cat_result.scalars().all()

        menu: list[dict] = []
        for category in categories:
            prod_result = await self._session.execute(
                select(Product)
                .where(
                    Product.category_id == category.id,
                    Product.is_active.is_(True),
                    or_(
                        Product.time_period_override.is_(None),
                        Product.time_period_override == "both",
                        Product.time_period_override == period,
                    ),
                )
                .order_by(Product.sort)
            )
            products = prod_result.scalars().all()
            menu.append(
                {
                    "category": category,
                    "products": products,
                }
            )
        return menu
