"""Order tools.

Session-boundary rule (CONSTRAINTS.md, cross-repo): tools never open their
own session. Session is injected via functools.partial at VM-build time
(see app/services/order_service.py::_build_vm). commit() happens once, at
the caller's boundary (OrderService), never inside a tool.

Terminal-step rule (CONSTRAINTS.md 2026-07-02): a terminal TOOL step with no
downstream CONDITION consuming its output must raise on failure, never
return a sentinel string — a swallowed "ERROR" silently leaves Trace.status
== SUCCESS. This bit Sieshka in production (order_tools.py, kitchen_tools.py,
inventory_tools.py) before it was fixed; writing it correctly the first time
here instead of retrofitting it.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.models import Order


async def create_order(
    session: AsyncSession,
    *,
    tenant_id: str,
    customer_telegram_id: int,
    items: dict[str, Any],
    total_amount: int,
) -> str:
    order = Order(
        tenant_id=uuid.UUID(tenant_id),
        customer_telegram_id=customer_telegram_id,
        items=items,
        total_amount=total_amount,
        state="DRAFT",
    )
    session.add(order)
    await session.flush()  # populate order.id, no commit — caller's boundary
    return str(order.id)


async def confirm_order(session: AsyncSession, *, order_id: str) -> str:
    """Terminal write. FOR UPDATE re-check mirrors the Sieshka
    write_order_state_* pattern — raise on any mismatch, never sentinel."""
    result = await session.execute(
        select(Order).where(Order.id == uuid.UUID(order_id)).with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"order {order_id} not found")
    if order.state != "DRAFT":
        raise ValueError(f"order {order_id} not in DRAFT (actual: {order.state})")

    order.state = "CONFIRMED"
    return "CONFIRMED"
