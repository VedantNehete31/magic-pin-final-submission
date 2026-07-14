from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def value(data: dict[str, Any] | None, path: str, default: Any = None) -> Any:
    current: Any = data or {}
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def first_present(*items: Any, default: Any = "") -> Any:
    for item in items:
        if item not in (None, "", [], {}):
            return item
    return default


def merchant_name(merchant: dict[str, Any]) -> str:
    return first_present(value(merchant, "identity.name"), merchant.get("name"), merchant.get("merchant_name"), default="your business")


def merchant_short_name(merchant: dict[str, Any], category_slug: str | None = None) -> str:
    owner = value(merchant, "identity.owner_first_name")
    name = merchant_name(merchant)
    if owner and category_slug == "dentists":
        if not str(owner).lower().startswith("dr"):
            return f"Dr. {owner}"
        return str(owner)
    if owner:
        return str(owner)
    cleaned = str(name).replace("'", " ").replace(",", " ")
    parts = [part for part in cleaned.split() if part.lower() not in {"clinic", "dental", "restaurant", "cafe", "salon", "gym", "pharmacy"}]
    return " ".join(parts[:2]) if parts else str(name)


def category_slug(category: dict[str, Any] | None, merchant: dict[str, Any] | None = None) -> str:
    return str(first_present(value(category, "slug"), value(merchant, "category_slug"), default="businesses"))


def languages_for(merchant: dict[str, Any] | None, customer: dict[str, Any] | None = None) -> list[str]:
    langs = value(merchant, "identity.languages", []) or []
    pref = str(value(customer, "identity.language_pref", "")).lower()
    if "hi" in pref or "hindi" in pref:
        return [*langs, "hi"]
    return list(langs)


def wants_hinglish(merchant: dict[str, Any] | None, customer: dict[str, Any] | None = None) -> bool:
    return any(str(lang).lower().startswith("hi") for lang in languages_for(merchant, customer))


def active_offer(merchant: dict[str, Any] | None, category: dict[str, Any] | None = None) -> str | None:
    for offer in value(merchant, "offers", []) or []:
        if str(offer.get("status", "")).lower() in {"active", "live", ""}:
            title = offer.get("title") or offer.get("name")
            if title:
                return str(title)
    for offer in value(category, "offer_catalog", []) or []:
        title = offer.get("title") or offer.get("name")
        if title:
            return str(title)
    return None


def digest_item(category: dict[str, Any] | None, trigger: dict[str, Any] | None) -> dict[str, Any] | None:
    items = value(category, "digest", []) or []
    top_id = first_present(value(trigger, "payload.top_item_id"), value(trigger, "payload.digest_item_id"), default=None)
    if top_id:
        for item in items:
            if item.get("id") == top_id:
                return item
    top_item = value(trigger, "payload.top_item")
    if isinstance(top_item, dict):
        return top_item
    return items[0] if items else None


def peer_ctr(category: dict[str, Any] | None) -> float | None:
    raw = value(category, "peer_stats.avg_ctr")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def merchant_ctr(merchant: dict[str, Any] | None) -> float | None:
    raw = value(merchant, "performance.ctr")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def percentage(raw: Any) -> str | None:
    try:
        return f"{float(raw) * 100:.0f}%"
    except (TypeError, ValueError):
        return None


def safe_join(parts: list[str]) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip()]
    text = " ".join(cleaned)
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def cta_for_action(kind: str) -> str:
    if kind in {"recall_due", "appointment_tomorrow", "customer_lapsed_soft", "customer_lapsed_hard", "chronic_refill_due"}:
        return "binary_yes_no"
    if kind in {"research_digest", "category_research_digest_release", "curious_ask_due", "active_planning_intent"}:
        return "open_ended"
    return "binary_yes_no"


def template_params(body: str, lead: str) -> list[str]:
    chunks = [chunk.strip() for chunk in body.replace("\n", " ").split(".") if chunk.strip()]
    params = [lead]
    params.extend(chunks[:2])
    return params[:4]


def parse_iso(value_text: str | None) -> datetime | None:
    if not value_text:
        return None
    try:
        return datetime.fromisoformat(value_text.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_expired(trigger: dict[str, Any], now_text: str | None) -> bool:
    expiry = parse_iso(trigger.get("expires_at"))
    now = parse_iso(now_text) or datetime.now(timezone.utc)
    if expiry is None:
        return False
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return expiry < now


def format_time(iso_str: str | None) -> str:
    if not iso_str:
        return "today"
    try:
        if "T" in iso_str:
            time_part = iso_str.split("T")[1]
            hours, minutes = time_part.split(":")[:2]
            h = int(hours)
            ampm = "PM" if h >= 12 else "AM"
            h_12 = h % 12
            if h_12 == 0:
                h_12 = 12
            return f"{h_12}:{minutes} {ampm} today"
    except Exception:
        pass
    return "today"

