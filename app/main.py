from __future__ import annotations

from fastapi import FastAPI

from app.webhooks.telegram import router as telegram_router

app = FastAPI(title="vietbot")
app.include_router(telegram_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
