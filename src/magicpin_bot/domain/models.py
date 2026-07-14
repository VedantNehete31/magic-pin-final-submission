from dataclasses import dataclass, field
from time import time
from typing import Any


ContextPayload = dict[str, Any]


@dataclass(frozen=True)
class StoredContext:
    version: int
    payload: ContextPayload
    delivered_at: str | None = None


@dataclass
class ConversationTurn:
    role: str
    body: str
    ts: str | None = None


@dataclass
class Conversation:
    conversation_id: str
    merchant_id: str | None = None
    customer_id: str | None = None
    trigger_id: str | None = None
    turns: list[ConversationTurn] = field(default_factory=list)
    sent_bodies: set[str] = field(default_factory=set)
    ended: bool = False
    auto_reply_count: int = 0


@dataclass(frozen=True)
class ComposedMessage:
    body: str
    cta: str
    send_as: str
    suppression_key: str
    rationale: str
    template_name: str = "vera_engagement_v1"
    template_params: list[str] = field(default_factory=list)


@dataclass
class RuntimeState:
    started_at: float = field(default_factory=time)

