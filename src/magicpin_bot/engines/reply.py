from __future__ import annotations

from magicpin_bot.config import settings
from magicpin_bot.domain.models import ConversationTurn
from magicpin_bot.engines.gemini import GeminiReplyGenerator
from magicpin_bot.services.context_store import ContextStore


class ReplyEngine:
    def __init__(self, store: ContextStore) -> None:
        self.store = store

    def reply(self, conversation_id: str, merchant_id: str | None, customer_id: str | None, from_role: str, message: str, received_at: str | None, turn_number: int) -> dict:
        conversation = self.store.conversation(conversation_id, merchant_id, customer_id)
        conversation.turns.append(ConversationTurn(role=from_role, body=message, ts=received_at))
        if conversation.ended:
            return self._end(conversation, "This conversation was already closed.")
        normalized = message.strip().lower()
        if self._is_opt_out(normalized):
            return self._end(conversation, "User explicitly opted out or rejected further messaging.")
        if self._is_hostile(normalized):
            return self._end(conversation, "User frustration is explicit, so the conversation is closed gracefully.")
        if self._is_auto_reply(normalized, conversation_id):
            return self._auto_reply_response(conversation, received_at)

        generated = GeminiReplyGenerator(self.store, settings).generate(conversation, message)
        if generated:
            return self._send(conversation, generated, "binary_send_edit" if self._is_confirmation(normalized) else "open_ended", "Gemini generated a context-grounded reply; deterministic safety rules ran first.", received_at)
        if self._is_confirmation(normalized):
            return self._send(conversation, "Confirmed. Here is the draft for your approval: \"Hi, I am reaching out with a quick update based on your current Vera context. Would you like me to send the next steps?\" Reply SEND to approve it, or EDIT with your changes.", "binary_send_edit", "The user confirmed, so the bot provides a reviewable draft for final approval.", received_at)
        if self._is_positive_intent(normalized):
            return self._send(conversation, "Great. I will move this to action now. Reply CONFIRM and I will prepare the draft with the latest context I have, then you can approve before anything is sent.", "binary_confirm_cancel", "User showed explicit intent, so the bot switches from persuasion to execution.", received_at)
        if self._is_off_topic(normalized):
            return self._send(conversation, "That is outside what I can handle directly. Coming back to this Vera task, should I draft the message or wait?", "open_ended", "Off-topic request politely declined while preserving the active conversation.", received_at)
        return self._send(conversation, "Got it. I can keep this simple: I will draft the next message from your current context, and you can approve before anything goes out. Should I prepare it?", "binary_yes_no", "Acknowledges the reply and offers one low-friction next step.", received_at)

    def _send(self, conversation, body: str, cta: str, rationale: str, received_at: str | None = None) -> dict:
        if body in conversation.sent_bodies:
            self.store.save_conversation(conversation)
            return {"action": "wait", "wait_seconds": 1800, "rationale": "The next available template would repeat a prior message, so the bot waits instead."}
        conversation.turns.append(ConversationTurn(role="bot", body=body, ts=received_at))
        conversation.sent_bodies.add(body)
        self.store.save_conversation(conversation)
        return {"action": "send", "body": body, "cta": cta, "rationale": rationale}

    def _end(self, conversation, rationale: str) -> dict:
        conversation.ended = True
        self.store.save_conversation(conversation)
        return {"action": "end", "rationale": rationale}

    def _is_auto_reply(self, text: str, conversation_id: str) -> bool:
        phrases = ["thank you for contacting", "thanks for contacting", "will respond shortly", "automated assistant", "currently away", "business hours"]
        if any(phrase in text for phrase in phrases):
            return True
        conversation = self.store.get_conversation(conversation_id)
        if not conversation:
            return False
        prior = [turn.body.strip().lower() for turn in conversation.turns[:-1] if turn.role in {"merchant", "customer"}]
        return prior.count(text) >= 1 and len(text) > 20

    def _auto_reply_response(self, conversation, received_at: str | None) -> dict:
        conversation.auto_reply_count += 1
        return self._end(conversation, "Detected a likely WhatsApp Business auto-reply, so the bot avoids adding another message.")

    def _is_opt_out(self, text: str) -> bool:
        return any(phrase in text for phrase in ["stop messaging", "stop message", "unsubscribe", "not interested", "do not message", "don't message", "no thanks", "remove me"])

    def _is_hostile(self, text: str) -> bool:
        return any(phrase in text for phrase in ["useless", "bothering me", "waste", "angry", "shut up"])

    def _is_positive_intent(self, text: str) -> bool:
        return any(phrase in text for phrase in ["yes", "go ahead", "let's do it", "lets do it", "send it", "do it", "join", "start", "ok"])

    def _is_confirmation(self, text: str) -> bool:
        return text in {"confirm", "confirmed", "yes, confirm", "yes confirm"}

    def _is_off_topic(self, text: str) -> bool:
        return any(phrase in text for phrase in ["gst", "tax", "income tax", "file return", "loan", "personal"])
