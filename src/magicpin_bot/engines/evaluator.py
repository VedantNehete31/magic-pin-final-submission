from __future__ import annotations

from magicpin_bot.domain.models import ComposedMessage


class EvaluationEngine:
    def validate(self, message: ComposedMessage, seen_bodies: set[str] | None = None) -> ComposedMessage | None:
        if not message.body.strip():
            return None
        if "http://" in message.body or "https://" in message.body:
            return None
        if message.body in (seen_bodies or set()):
            return None
        if not message.suppression_key:
            return None
        if message.cta not in {"binary_yes_no", "open_ended", "none", "multi_choice_slot", "binary_confirm_cancel"}:
            return None
        return message

