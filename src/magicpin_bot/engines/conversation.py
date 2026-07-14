from __future__ import annotations

from magicpin_bot.domain.models import ConversationTurn
from magicpin_bot.engines.composer import Composer
from magicpin_bot.engines.decision import DecisionEngine
from magicpin_bot.engines.evaluator import EvaluationEngine
from magicpin_bot.services.context_store import ContextStore


class ConversationEngine:
    def __init__(self, store: ContextStore) -> None:
        self.store = store
        self.decisions = DecisionEngine(store)
        self.composer = Composer()
        self.evaluator = EvaluationEngine()

    def tick(self, now: str | None, available_triggers: list[str]) -> list[dict]:
        actions: list[dict] = []
        for candidate in self.decisions.candidates(available_triggers, now):
            message = self.composer.compose(candidate.category, candidate.merchant, candidate.trigger, candidate.customer)
            customer_id = candidate.customer.get("customer_id") if candidate.customer else None
            conversation_id = self._conversation_id(candidate.merchant.get("merchant_id"), customer_id, candidate.trigger_id)
            conversation = self.store.conversation(conversation_id, candidate.merchant.get("merchant_id"), customer_id, candidate.trigger_id)
            validated = self.evaluator.validate(message, conversation.sent_bodies)
            if not validated:
                continue
            conversation.sent_bodies.add(validated.body)
            conversation.turns.append(ConversationTurn(role=validated.send_as, body=validated.body, ts=now))
            self.store.mark_suppressed(validated.suppression_key)
            self.store.save_conversation(conversation)
            actions.append({
                "conversation_id": conversation_id,
                "merchant_id": candidate.merchant.get("merchant_id"),
                "customer_id": customer_id,
                "send_as": validated.send_as,
                "trigger_id": candidate.trigger_id,
                "template_name": validated.template_name,
                "template_params": validated.template_params,
                "body": validated.body,
                "cta": validated.cta,
                "suppression_key": validated.suppression_key,
                "rationale": validated.rationale,
            })
        return actions

    def _conversation_id(self, merchant_id: str | None, customer_id: str | None, trigger_id: str) -> str:
        if customer_id:
            return f"conv_{customer_id}_{trigger_id}".replace(" ", "_")
        return f"conv_{merchant_id}_{trigger_id}".replace(" ", "_")

