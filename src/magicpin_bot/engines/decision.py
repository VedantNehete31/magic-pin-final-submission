from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from magicpin_bot.engines.context_tools import is_expired
from magicpin_bot.services.context_store import ContextStore


@dataclass(frozen=True)
class Candidate:
    trigger_id: str
    trigger: dict[str, Any]
    merchant: dict[str, Any]
    category: dict[str, Any]
    customer: dict[str, Any] | None = None


class DecisionEngine:
    def __init__(self, store: ContextStore) -> None:
        self.store = store

    def candidates(self, trigger_ids: list[str], now: str | None, limit: int = 20) -> list[Candidate]:
        result: list[Candidate] = []
        for trigger_id in trigger_ids:
            trigger = self.store.get_context("trigger", trigger_id)
            if not trigger or is_expired(trigger, now):
                continue
            suppression_key = str(trigger.get("suppression_key") or trigger.get("id") or trigger_id)
            if suppression_key in self.store.sent_suppression_keys:
                continue
            merchant_id = trigger.get("merchant_id") or (trigger.get("payload") or {}).get("merchant_id")
            merchant = self.store.get_context("merchant", merchant_id)
            if not merchant:
                continue
            category_id = merchant.get("category_slug") or (trigger.get("payload") or {}).get("category")
            category = self.store.get_context("category", category_id)
            if not category:
                continue
            customer_id = trigger.get("customer_id") or (trigger.get("payload") or {}).get("customer_id")
            customer = self.store.get_context("customer", customer_id)
            if trigger.get("scope") == "customer":
                if not customer or not self._has_customer_consent(customer, str(trigger.get("kind") or "")):
                    continue
            result.append(Candidate(trigger_id=trigger_id, trigger=trigger, merchant=merchant, category=category, customer=customer))
        result.sort(key=lambda item: int(item.trigger.get("urgency") or 0), reverse=True)
        return result[:limit]
    def _has_customer_consent(self, customer: dict[str, Any], trigger_kind: str) -> bool:
        consent = customer.get("consent") or {}
        preferences = customer.get("preferences") or {}
        scopes = set(consent.get("scope") or [])
        required_scopes = {
            "recall_due": "recall_reminders",
            "appointment_tomorrow": "appointment_reminders",
            "chronic_refill_due": "refill_reminders",
            "customer_lapsed_hard": "winback_offers",
            "customer_lapsed_soft": "winback_offers",
            "wedding_package_followup": "bridal_package_followup",
            "trial_followup": "kids_program_updates",
        }
        required_scope = required_scopes.get(trigger_kind.lower())
        return preferences.get("reminder_opt_in") is not False and bool(scopes) and (not required_scope or required_scope in scopes)
