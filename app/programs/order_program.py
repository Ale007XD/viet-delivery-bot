"""order_program: create_order -> confirm_order.

Deliberately no LLM step yet (MVP = structured Telegram button flow, not
free-text). classify_intent-style LLM step is a later addition once the bot
needs to parse free-text orders — CONSTRAINTS.md's normalize_output pattern
applies then, not before it's needed (anti-sprawl, R12).
"""

from __future__ import annotations

from nano_vm.models import Program, Step

order_program = Program(
    name="create_and_confirm_order",
    steps=[
        Step(
            id="create_order",
            kind="TOOL",
            tool_name="create_order",
            args={
                "tenant_id": "$ctx.tenant_id",
                "customer_telegram_id": "$ctx.customer_telegram_id",
                "items": "$ctx.items",
                "total_amount": "$ctx.total_amount",
            },
            next_step="confirm_order",
        ),
        Step(
            id="confirm_order",
            kind="TOOL",
            tool_name="confirm_order",
            args={"order_id": "$create_order.output"},
            is_terminal=True,
        ),
    ],
)
