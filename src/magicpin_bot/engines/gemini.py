from __future__ import annotations

import json

import httpx

from magicpin_bot.config import Settings
from magicpin_bot.domain.models import Conversation
from magicpin_bot.services.context_store import ContextStore


class GeminiReplyGenerator:
    """Optional Gemini adapter. Returning None keeps the deterministic fallback active."""

    def __init__(self, store: ContextStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    def generate(self, conversation: Conversation, message: str) -> str | None:
        if not self.settings.gemini_api_key:
            return None

        merchant = self.store.get_context("merchant", conversation.merchant_id) or {}
        customer = self.store.get_context("customer", conversation.customer_id) or {}
        history = [
            {"role": turn.role, "message": turn.body}
            for turn in conversation.turns[-8:]
        ]
        prompt = (
            "Write the next reply only, without labels or markdown. You are Vera, a helpful "
            "Magicpin business assistant. Keep it under 70 words, natural and specific to the "
            "conversation. Do not invent offers, performance numbers, customer facts, actions, "
            "or approvals. Do not claim anything was sent. If the user is confirming, provide "
            "a concise reviewable draft and ask for SEND or EDIT.\n\n"
            f"Merchant context: {json.dumps(merchant, ensure_ascii=True)}\n"
            f"Customer context: {json.dumps(customer, ensure_ascii=True)}\n"
            f"Recent conversation: {json.dumps(history, ensure_ascii=True)}\n"
            f"Latest user message: {message}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 180, "temperature": 0},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        try:
            response = httpx.post(
                url,
                headers={"x-goog-api-key": self.settings.gemini_api_key},
                json=payload,
                timeout=12.0,
            )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            return None
        return text or None