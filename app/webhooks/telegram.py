from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domains.models import TenantBot

router = APIRouter()


@router.post("/webhooks/telegram/{bot_slug}")
async def telegram_webhook(
    bot_slug: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, str]:
    result = await session.execute(
        select(TenantBot).where(TenantBot.bot_slug == bot_slug, TenantBot.is_active.is_(True))
    )
    tenant_bot = result.scalar_one_or_none()
    if tenant_bot is None:
        # 404, not 401 — don't confirm/deny bot_slug existence to a stranger
        raise HTTPException(status_code=404)

    if x_telegram_bot_api_secret_token != tenant_bot.webhook_secret:
        raise HTTPException(status_code=401)

    update = await request.json()
    message = update.get("message") or update.get("callback_query", {}).get("message")
    if message is None:
        return {"ok": "true"}  # unrecognized update type, ack anyway

    # MVP wiring placeholder — real order payload comes from a WebApp/inline
    # keyboard flow, not parsed here. Left explicit rather than stubbed
    # silently so the next session sees exactly where to continue.
    if update.get("message", {}).get("text") == "/start":
        # TODO: send tenant-branded welcome message via Bot API sendMessage
        pass

    return {"ok": "true"}
