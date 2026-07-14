from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from magicpin_bot.config import settings
from magicpin_bot.engines.conversation import ConversationEngine
from magicpin_bot.engines.reply import ReplyEngine
from magicpin_bot.services.context_store import store


app = FastAPI(title=settings.team_name, version=settings.version)


class ContextRequest(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: dict[str, Any]
    delivered_at: str | None = None


class TickRequest(BaseModel):
    now: str
    available_triggers: list[str] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: str | None = None
    customer_id: str | None = None
    from_role: str
    message: str
    received_at: str
    turn_number: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@app.get("/v1/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "uptime_seconds": store.uptime_seconds(),
        "contexts_loaded": store.counts(),
    }


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": settings.team_name,
        "status": "running",
        "healthz": "/v1/healthz",
        "metadata": "/v1/metadata",
    }


@app.get("/v1/metadata")
async def metadata() -> dict[str, Any]:
    return {
        "team_name": settings.team_name,
        "team_members": settings.team_members,
        "model": settings.model,
        "approach": settings.approach,
        "contact_email": settings.contact_email,
        "version": settings.version,
        "submitted_at": settings.submitted_at,
    }


@app.post("/v1/context")
async def context(body: ContextRequest) -> dict[str, Any]:
    if body.scope not in {"category", "merchant", "customer", "trigger"}:
        raise HTTPException(status_code=400, detail={"accepted": False, "reason": "invalid_scope"})
    accepted, current_version = store.upsert_context(body.scope, body.context_id, body.version, body.payload, body.delivered_at)
    if not accepted:
        raise HTTPException(status_code=409, detail={"accepted": False, "reason": "stale_version", "current_version": current_version})
    return {"accepted": True, "ack_id": f"ack_{body.context_id}_v{body.version}", "stored_at": utc_now()}


@app.post("/v1/tick")
async def tick(body: TickRequest) -> dict[str, Any]:
    return {"actions": ConversationEngine(store).tick(body.now, body.available_triggers)}


@app.post("/v1/reply")
async def reply(body: ReplyRequest) -> dict[str, Any]:
    return ReplyEngine(store).reply(
        body.conversation_id,
        body.merchant_id,
        body.customer_id,
        body.from_role,
        body.message,
        body.received_at,
        body.turn_number,
    )


@app.post("/v1/teardown")
async def teardown() -> dict[str, bool]:
    store.reset()
    return {"accepted": True}
