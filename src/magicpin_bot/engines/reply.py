from __future__ import annotations

from magicpin_bot.config import settings
from magicpin_bot.domain.models import ConversationTurn
from magicpin_bot.engines.gemini import GeminiReplyGenerator
from magicpin_bot.services.context_store import ContextStore
from magicpin_bot.engines.context_tools import wants_hinglish


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

        # Determine if customer-scoped conversation
        is_customer = (customer_id is not None) or (from_role == "customer")

        if is_customer:
            cust = self.store.get_context("customer", customer_id) if customer_id else {}
            merch = self.store.get_context("merchant", merchant_id) if merchant_id else {}
            
            # Off-topic checks for customer
            if self._is_off_topic(normalized):
                body = "That is outside what I can help you with. Please contact the business directly."
                return self._send(conversation, body, "none", "Customer off-topic request handled.", received_at)
                
            # Booking or positive intent checks for customer
            if self._is_positive_intent(normalized) or "slot" in normalized or "book" in normalized or any(char.isdigit() for char in normalized):
                if wants_hinglish(merch, cust):
                    body = "Thank you for confirming! Aapka slot book ho gaya hai. Hum aapko details jald hi send karenge."
                else:
                    body = "Thank you for confirming! Your slot has been booked. We will send you the details shortly."
                return self._send(conversation, body, "none", "Customer confirmed booking request.", received_at)
                
            # Fallback check-in for customer general messages
            if wants_hinglish(merch, cust):
                body = "Thank you for your message. Hum aapse jald hi contact karenge."
            else:
                body = "Thank you for your message. We will get back to you shortly."
            return self._send(conversation, body, "none", "Customer message acknowledged.", received_at)

        # Merchant reply flows
        generated = GeminiReplyGenerator(self.store, settings).generate(conversation, message)
        if generated:
            return self._send(conversation, generated, "binary_send_edit" if self._is_confirmation(normalized) else "open_ended", "Gemini generated a context-grounded reply; deterministic safety rules ran first.", received_at)
        if self._is_confirmation(normalized):
            return self._send(conversation, "Confirmed. Here is the draft for your approval: \"Hi, I am reaching out with a quick update based on your current Vera context. Would you like me to send the next steps?\" Reply SEND to approve it, or EDIT with your changes.", "binary_send_edit", "The user confirmed, so the bot provides a reviewable draft for final approval.", received_at)
        if self._is_positive_intent(normalized):
            return self._send(conversation, "Great. I will move this to action now. Reply CONFIRM and I will prepare the draft with the latest context I have, then you can approve before anything is sent.", "binary_confirm_cancel", "User showed explicit intent, so the bot switches from persuasion to execution.", received_at)
        if self._is_off_topic(normalized):
            body = self._handle_off_topic(normalized, is_customer=False)
            return self._send(conversation, body, "open_ended", "Off-topic request politely declined while preserving the active conversation.", received_at)
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
        if conversation.auto_reply_count == 1:
            return self._send(conversation, "Looks like an auto-reply. When the owner sees this, just reply YES and I will handle the draft.", "binary_yes_no", "Detected a likely WhatsApp Business auto-reply and left one owner-facing prompt.", received_at)
        if conversation.auto_reply_count == 2:
            self.store.save_conversation(conversation)
            return {"action": "wait", "wait_seconds": 86400, "rationale": "Same auto-reply pattern repeated, so the bot backs off for 24 hours."}
        return self._end(conversation, "Auto-reply repeated multiple times with no real engagement, so the conversation is closed.")

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

    def _handle_off_topic(self, text: str, is_customer: bool) -> str:
        if is_customer:
            return "That is outside what I can help you with. Please contact the business directly."
        
        if "gst" in text:
            return "I cannot handle GST filing or tax queries, as that is outside what I can handle directly. Coming back to this marketing task, should I draft the message or wait?"
        if "tax" in text or "return" in text:
            return "I cannot handle tax filing or financial returns, as that is outside what I can handle directly. Coming back to this marketing task, should I draft the message or wait?"
        if "loan" in text or "personal" in text:
            return "I cannot assist with loans or personal queries, as that is outside what I can handle directly. Coming back to this marketing task, should I draft the message or wait?"
            
        return "That is outside what I can handle directly. Coming back to this marketing task, should I draft the message or wait?"
