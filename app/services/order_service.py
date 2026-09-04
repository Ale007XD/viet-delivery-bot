from __future__ import annotations

import functools
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.programs.order_program import order_program
from app.tools import order_tools

# Tools that write to the DB and therefore need the request-scoped session
# injected via closure — never call app.db.async_session_factory() directly
# inside a tool (CONSTRAINTS.md: Tool-authoring session boundary rule).
_SESSION_TOOLS = {"create_order", "confirm_order"}


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _build_tools(self) -> dict[str, Any]:
        return {
            "create_order": functools.partial(order_tools.create_order, self._session),
            "confirm_order": functools.partial(order_tools.confirm_order, self._session),
        }

    async def place_order(
        self,
        *,
        tenant_id: str,
        customer_telegram_id: int,
        items: dict[str, Any],
        total_amount: int,
    ) -> str:
        from nano_vm.vm import ExecutionVM  # local import: keep nano_vm optional at module load

        vm = ExecutionVM(program=order_program, tools=self._build_tools())
        trace = await vm.run(
            context={
                "tenant_id": tenant_id,
                "customer_telegram_id": customer_telegram_id,
                "items": items,
                "total_amount": total_amount,
            }
        )
        # Single commit at the transition boundary — not inside any tool.
        await self._session.commit()
        return str(trace.trace_id)
