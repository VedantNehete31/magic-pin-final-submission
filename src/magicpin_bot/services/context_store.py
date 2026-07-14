from __future__ import annotations

import json
import os
from time import time
from typing import Any

from magicpin_bot.domain.models import Conversation, ConversationTurn, RuntimeState, StoredContext


class MemoryContextStore:
    """Local development store. Production uses Redis when REDIS_URL is configured."""

    def __init__(self) -> None:
        self.contexts: dict[tuple[str, str], StoredContext] = {}
        self.conversations: dict[str, Conversation] = {}
        self.sent_suppression_keys: set[str] = set()
        self.state = RuntimeState()

    def upsert_context(self, scope: str, context_id: str, version: int, payload: dict[str, Any], delivered_at: str | None) -> tuple[bool, int | None]:
        key = (scope, context_id)
        current = self.contexts.get(key)
        if current and current.version > version:
            return False, current.version
        if scope == "trigger":
            suppression_key = str(payload.get("suppression_key") or payload.get("id") or context_id)
            self.sent_suppression_keys.discard(suppression_key)
            conv_ids_to_del = [cid for cid in self.conversations if context_id in cid]
            for cid in conv_ids_to_del:
                del self.conversations[cid]
        if current and current.version == version:
            return True, current.version
        self.contexts[key] = StoredContext(version=version, payload=payload, delivered_at=delivered_at)
        return True, None

    def get_context(self, scope: str, context_id: str | None) -> dict[str, Any] | None:
        stored = self.contexts.get((scope, context_id)) if context_id else None
        return stored.payload if stored else None

    def counts(self) -> dict[str, int]:
        result = {"category": 0, "merchant": 0, "customer": 0, "trigger": 0}
        for scope, _ in self.contexts:
            result[scope] = result.get(scope, 0) + 1
        return result

    def uptime_seconds(self) -> int:
        return int(time() - self.state.started_at)

    def conversation(self, conversation_id: str, merchant_id: str | None = None, customer_id: str | None = None, trigger_id: str | None = None) -> Conversation:
        current = self.conversations.get(conversation_id)
        if current:
            return current
        current = Conversation(conversation_id=conversation_id, merchant_id=merchant_id, customer_id=customer_id, trigger_id=trigger_id)
        self.conversations[conversation_id] = current
        return current

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.conversations.get(conversation_id)

    def save_conversation(self, conversation: Conversation) -> None:
        self.conversations[conversation.conversation_id] = conversation

    def is_suppressed(self, suppression_key: str) -> bool:
        return suppression_key in self.sent_suppression_keys

    def mark_suppressed(self, suppression_key: str) -> None:
        self.sent_suppression_keys.add(suppression_key)

    def reset(self) -> None:
        self.contexts.clear()
        self.conversations.clear()
        self.sent_suppression_keys.clear()
        self.state = RuntimeState()


class RedisContextStore:
    """Redis-backed state for restart-safe deployments."""

    prefix = "magicpin_vera"

    def __init__(self, url: str) -> None:
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Redis state requires the redis package. Install requirements.txt first.") from exc
        self.client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=3, socket_timeout=3)
        self.client.ping()
        self.state = RuntimeState()

    def _key(self, *parts: str) -> str:
        return ":".join((self.prefix, *parts))

    def upsert_context(self, scope: str, context_id: str, version: int, payload: dict[str, Any], delivered_at: str | None) -> tuple[bool, int | None]:
        if scope == "trigger":
            suppression_key = str(payload.get("suppression_key") or payload.get("id") or context_id)
            self.client.srem(self._key("suppression_keys"), suppression_key)
            pattern = self._key("conversation", f"*{context_id}*")
            conv_keys = list(self.client.scan_iter(match=pattern))
            if conv_keys:
                self.client.delete(*conv_keys)
        key = self._key("context", scope, context_id)
        current_raw = self.client.get(key)
        if current_raw:
            current = json.loads(current_raw)
            current_version = int(current["version"])
            if current_version > version:
                return False, current_version
            if current_version == version:
                return True, current_version
        self.client.set(key, json.dumps({"version": version, "payload": payload, "delivered_at": delivered_at}, ensure_ascii=True))
        self.client.sadd(self._key("context_ids", scope), context_id)
        return True, None

    def get_context(self, scope: str, context_id: str | None) -> dict[str, Any] | None:
        if not context_id:
            return None
        raw = self.client.get(self._key("context", scope, context_id))
        return json.loads(raw)["payload"] if raw else None

    def counts(self) -> dict[str, int]:
        return {scope: int(self.client.scard(self._key("context_ids", scope))) for scope in ("category", "merchant", "customer", "trigger")}

    def uptime_seconds(self) -> int:
        return int(time() - self.state.started_at)

    def conversation(self, conversation_id: str, merchant_id: str | None = None, customer_id: str | None = None, trigger_id: str | None = None) -> Conversation:
        current = self.get_conversation(conversation_id)
        if current:
            return current
        current = Conversation(conversation_id=conversation_id, merchant_id=merchant_id, customer_id=customer_id, trigger_id=trigger_id)
        self.save_conversation(current)
        return current

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        raw = self.client.get(self._key("conversation", conversation_id))
        if not raw:
            return None
        data = json.loads(raw)
        return Conversation(
            conversation_id=data["conversation_id"], merchant_id=data.get("merchant_id"), customer_id=data.get("customer_id"), trigger_id=data.get("trigger_id"),
            turns=[ConversationTurn(**turn) for turn in data.get("turns", [])], sent_bodies=set(data.get("sent_bodies", [])),
            ended=bool(data.get("ended", False)), auto_reply_count=int(data.get("auto_reply_count", 0)),
        )

    def save_conversation(self, conversation: Conversation) -> None:
        data = {
            "conversation_id": conversation.conversation_id, "merchant_id": conversation.merchant_id, "customer_id": conversation.customer_id, "trigger_id": conversation.trigger_id,
            "turns": [{"role": turn.role, "body": turn.body, "ts": turn.ts} for turn in conversation.turns],
            "sent_bodies": sorted(conversation.sent_bodies), "ended": conversation.ended, "auto_reply_count": conversation.auto_reply_count,
        }
        self.client.set(self._key("conversation", conversation.conversation_id), json.dumps(data, ensure_ascii=True))
        self.client.sadd(self._key("conversation_ids"), conversation.conversation_id)

    def is_suppressed(self, suppression_key: str) -> bool:
        return bool(self.client.sismember(self._key("suppression_keys"), suppression_key))

    def mark_suppressed(self, suppression_key: str) -> None:
        self.client.sadd(self._key("suppression_keys"), suppression_key)

    def reset(self) -> None:
        keys: list[str] = []
        for pattern in (self._key("context", "*"), self._key("context_ids", "*"), self._key("conversation", "*"), self._key("conversation_ids"), self._key("suppression_keys")):
            keys.extend(self.client.scan_iter(match=pattern))
        if keys:
            self.client.delete(*keys)
        self.state = RuntimeState()


ContextStore = MemoryContextStore | RedisContextStore


def build_store():
    url = os.getenv("REDIS_URL")
    return RedisContextStore(url) if url else MemoryContextStore()


store = build_store()