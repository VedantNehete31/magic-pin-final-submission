from __future__ import annotations

from typing import Any, Optional

from magicpin_bot.domain.models import ComposedMessage
from magicpin_bot.engines.challenge_composer import ChallengeComposer
from magicpin_bot.engines.context_tools import active_offer, category_slug, cta_for_action, digest_item, first_present, merchant_ctr, merchant_name, merchant_short_name, peer_ctr, percentage, safe_join, template_params, value, wants_hinglish, format_time


def compose(category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any] | None = None) -> dict[str, Any]:
    message = Composer().compose(category, merchant, trigger, customer)
    return {
        "body": message.body,
        "cta": message.cta,
        "send_as": message.send_as,
        "suppression_key": message.suppression_key,
        "rationale": message.rationale,
    }


class Composer:
    def compose(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any] | None = None) -> ComposedMessage:
        special = ChallengeComposer().compose(category, merchant, trigger, customer)
        if special:
            return special
        kind = str(trigger.get("kind") or "").lower()
        if customer or trigger.get("scope") == "customer":
            return self._compose_customer(category, merchant, trigger, customer)
        if kind in {"research_digest", "category_research_digest_release", "research_digest_release"}:
            return self._research_digest(category, merchant, trigger)
        if kind in {"perf_spike", "performance_spike", "perf_dip", "performance_dip", "seasonal_perf_dip"}:
            return self._performance(category, merchant, trigger)
        if kind in {"curious_ask_due", "scheduled_recurring"}:
            return self._curious_ask(category, merchant, trigger)
        if kind in {"festival_upcoming", "weather_heatwave", "local_news_event", "ipl_match_today", "category_trend_movement", "competitor_opened", "review_theme_emerged", "milestone_reached"}:
            return self._event(category, merchant, trigger)
        return self._generic_merchant(category, merchant, trigger)

    def _research_digest(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        slug = category_slug(category, merchant)
        item = digest_item(category, trigger) or {}
        name = merchant_short_name(merchant, slug)
        title = first_present(item.get("title"), value(trigger, "payload.title"), default="a new category update")
        source = first_present(item.get("source"), value(trigger, "payload.source"), default="")
        trial_n = first_present(item.get("trial_n"), value(trigger, "payload.trial_n"), default=None)
        segment = first_present(item.get("patient_segment"), value(trigger, "payload.patient_segment"), default="")
        segment_text = self._segment_text(segment, merchant)
        
        trial_text = ""
        if trial_n:
            try:
                trial_text = f"({int(trial_n):,}-person trial)"
            except (ValueError, TypeError):
                trial_text = f"({trial_n} trial)"
            
        if wants_hinglish(merchant):
            body = safe_join([
                f"{name}, {source + ' ' if source else ''}par research update hai: '{title}' {trial_text}.",
                segment_text,
                "Kya main iska summary aur patient WhatsApp outreach checklist draft karu?",
            ])
        else:
            body = safe_join([
                f"{name}, research update from {source}: '{title}' {trial_text}.",
                segment_text,
                "Want me to draft a patient WhatsApp outreach and a recall checklist for your clinic?",
            ])
            
        rationale = "Research trigger grounded in the category digest, with a source-backed hook and low-friction draft offer."
        return self._message(body, "open_ended", "vera", trigger, "vera_research_digest_v1", rationale, name)

    def _performance(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        slug = category_slug(category, merchant)
        name = merchant_short_name(merchant, slug)
        perf = value(merchant, "performance", {}) or {}
        
        payload = trigger.get("payload") or {}
        views = first_present(payload.get("views"), value(merchant, "performance.views"), default=None)
        calls = first_present(payload.get("calls"), value(merchant, "performance.calls"), default=None)
        directions = first_present(payload.get("directions"), value(merchant, "performance.directions"), default=None)
        
        m_ctr = merchant_ctr(merchant)
        p_ctr = peer_ctr(category)
        
        metric = payload.get("metric")
        delta_pct = payload.get("delta_pct")
        vs_baseline = payload.get("vs_baseline")
        likely_driver = payload.get("likely_driver")
        
        kind = str(trigger.get("kind", "")).lower()
        is_dip = "dip" in kind
        
        # Map corporate/internal jargon to merchant-appropriate terms
        metric_clean = str(metric or "").replace("calls", "phone inquiries").replace("views", "page views").replace("directions", "direction requests")
        driver_text = f", likely driven by {str(likely_driver).replace('_', ' ')}" if likely_driver else ""
        
        # Clean negative numbers for delta display
        pct_text = ""
        if delta_pct is not None:
            pct_val = abs(int(float(delta_pct) * 100))
            pct_text = f"{pct_val}%"
            
        if wants_hinglish(merchant):
            if is_dip:
                if metric and delta_pct is not None:
                    baseline_text = f" (average {vs_baseline} ke baseline se)" if vs_baseline is not None else ""
                    lead = f"{name}, quick heads-up: aapke {metric_clean} is week {pct_text} drop hue hain{baseline_text}{driver_text}."
                else:
                    lead = f"{name}, quick heads-up: visitor traffic and calls mein dip dekha gaya hai."
                action = "Kya main dynamic post draft karu aapke best active offer ke sath recovery drive karne ke liye?"
            else:
                if metric and delta_pct is not None:
                    baseline_text = f" (vs baseline of {vs_baseline})" if vs_baseline is not None else ""
                    lead = f"{name}, nice signal: aapke {metric_clean} is week {pct_text} increase hue hain{baseline_text}{driver_text}!"
                else:
                    lead = f"{name}, nice signal: metrics mein growth dikh raha hai!"
                action = "Kya main is traffic spike ko fresh Google post mein convert karu?"
        else:
            if is_dip:
                if metric and delta_pct is not None:
                    baseline_text = f" compared to your average of {vs_baseline}" if vs_baseline is not None else ""
                    lead = f"{name}, quick heads-up: your {metric_clean} dropped by {pct_text} this week{baseline_text}{driver_text}."
                else:
                    lead = f"{name}, quick heads-up: page traffic and inquiries have slowed down this week."
                action = "Want me to draft a recovery post using your best current offer?"
            else:
                if metric and delta_pct is not None:
                    baseline_text = f" compared to your average of {vs_baseline}" if vs_baseline is not None else ""
                    lead = f"{name}, nice signal: your {metric_clean} increased by {pct_text} this week{baseline_text}{driver_text}!"
                else:
                    lead = f"{name}, nice signal: page views and phone inquiries are trending up!"
                action = "Want me to turn this spike into a Google post while attention is warm?"
                
        facts = []
        if not metric or delta_pct is None:
            if views is not None:
                facts.append(f"{views} views")
            if calls is not None:
                facts.append(f"{calls} calls")
            if directions is not None:
                facts.append(f"{directions} direction requests")
            delta = first_present(value(perf, "delta_7d.views_pct"), value(perf, "delta_7d.calls_pct"), default=None)
            delta_text = percentage(delta)
            if delta_text:
                clean_delta_text = delta_text.replace("-", "")
                if wants_hinglish(merchant):
                    facts.append(f"is week {clean_delta_text} change")
                else:
                    facts.append(f"{clean_delta_text} change this week")
                
        ctr_text = ""
        if m_ctr is not None and p_ctr is not None:
            if wants_hinglish(merchant):
                ctr_text = f" Aapka CTR {m_ctr * 100:.1f}% hai vs peer {p_ctr * 100:.1f}%."
            else:
                ctr_text = f" Your CTR is {m_ctr * 100:.1f}% vs peer {p_ctr * 100:.1f}%."
                
        offer = active_offer(merchant, category)
        offer_text = ""
        if offer:
            if wants_hinglish(merchant):
                offer_text = f" Hum offer '{offer}' ko ready hook ki tarah use kar sakte hain."
            else:
                offer_text = f" We can use {offer} as the hook."
                
        body = safe_join([lead, ", ".join(facts) + "." if facts else "", ctr_text, offer_text, action])
        rationale = "Performance trigger uses dashboard numbers, peer comparison when available, and one concrete next action."
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_performance_v1", rationale, name)

    def _curious_ask(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        slug = category_slug(category, merchant)
        name = merchant_short_name(merchant, slug)
        business = merchant_name(merchant)
        offer = active_offer(merchant, category)
        hint = f" Is it around {offer}?" if offer else ""
        
        if wants_hinglish(merchant):
            body = f"Hi {name}, quick check - {business} mein is week customers sabse zyada kya pooch rahe hain?{hint} Main us answer ko Google post + 4-line WhatsApp reply bana dunga. 5 min ka kaam."
        else:
            body = f"Hi {name}, quick check - what service are customers asking about most this week at {business}?{hint} I can turn your answer into a Google post + 4-line WhatsApp reply. Takes 5 min."
            
        rationale = "Curious-ask trigger uses the merchant as the source and offers to do the work after one low-effort reply."
        return self._message(body, "open_ended", "vera", trigger, "vera_curious_ask_v1", rationale, name)

    def _event(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        slug = category_slug(category, merchant)
        name = merchant_short_name(merchant, slug)
        payload = trigger.get("payload") or {}
        
        title = first_present(
            payload.get("title"),
            payload.get("event"),
            payload.get("headline"),
            payload.get("query"),
            payload.get("festival"),
            payload.get("match"),
            payload.get("theme"),
            trigger.get("kind"),
            default="today's update"
        )
        
        locality = first_present(value(merchant, "identity.locality"), value(merchant, "identity.city"), default="your area")
        offer = active_offer(merchant, category)
        
        if offer:
            if wants_hinglish(merchant):
                offer_text = f" Aapka current offer '{offer}' ready hook hai."
            else:
                offer_text = f" Your current {offer} gives us a ready hook."
        else:
            offer_text = ""
            
        kind = str(trigger.get("kind", "")).lower()
        days_until = payload.get("days_until")
        date_val = payload.get("date")
        
        # Logical event title mapping (preventing future event timing errors)
        is_fest = "festival" in kind or payload.get("festival")
        is_match = payload.get("match")
        
        if is_match:
            time_iso = payload.get("match_time_iso")
            time_clean = format_time(time_iso)
            venue = payload.get("venue") or "stadium"
            title_text = f"the {title} match at {venue} starting at {time_clean}"
        else:
            title_text = f"{title}"
            
        if wants_hinglish(merchant):
            if kind == "competitor_opened":
                detail = first_present(payload.get("distance_km"), payload.get("distance"), default="nearby")
                comp = payload.get("competitor_name") or "competitor"
                body = f"{name}, {locality} mein new competitor '{comp}' open hua hai around {detail} km away. Kya main custom profile refreshment checklist taiyar karu is week competitive edge ke liye?"
            elif kind == "review_theme_emerged":
                theme = first_present(payload.get("theme"), default="review trend")
                body = f"{name}, {merchant_name(merchant)} ke recent reviews mein '{theme}' theme notice kiya gaya hai. Kya main client reply draft and team SOP checklist ready karu?"
            elif kind == "milestone_reached":
                milestone = first_present(payload.get("milestone"), payload.get("value_now"), default="milestone")
                body = f"{name}, {merchant_name(merchant)} ne '{milestone}' reviews milestone hit kiya hai. Kya main isko thank-you post aur booking reminder template mein change karu?"
            elif is_fest and days_until is not None:
                body = f"{name}, {title} is coming up in {days_until} days (on {date_val}) aapke business ke liye.{offer_text} Kya main early festive prep ke liye campaign draft karu?"
            else:
                body = f"{name}, {title_text} aapke area ({locality}) ke liye aaj relevant hai.{offer_text} Kya main update WhatsApp and Google post draft karu?"
        else:
            if kind == "competitor_opened":
                detail = first_present(payload.get("distance_km"), payload.get("distance"), default="nearby")
                comp = payload.get("competitor_name") or "competitor"
                body = f"{name}, new competitor signal in {locality}: '{comp}' opened {detail} km away. Want me to draft a profile refresh that makes your strongest service stand out this week?"
            elif kind == "review_theme_emerged":
                theme = first_present(payload.get("theme"), default="a repeated review theme")
                body = f"{name}, '{theme}' showed up in recent reviews for {merchant_name(merchant)}. Want me to draft a calm owner response + a small operations note for your team?"
            elif kind == "milestone_reached":
                milestone = first_present(payload.get("milestone"), payload.get("value_now"), default="a new milestone")
                body = f"{name}, {merchant_name(merchant)} just hit {milestone}. Want me to turn it into a thank-you Google post that also nudges the next booking?"
            elif is_fest and days_until is not None:
                body = f"{name}, {title} is coming up in {days_until} days (on {date_val}) for your area.{offer_text} Want me to draft a preliminary campaign plan to start early festival preparations?"
            else:
                body = f"{name}, {title_text} is relevant for {locality} today.{offer_text} Want me to draft one timely WhatsApp + Google post around it?"
                
        rationale = "External or internal event trigger converted into a timely merchant action without adding unsupported facts."
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_event_v1", rationale, name)

    def _generic_merchant(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        slug = category_slug(category, merchant)
        name = merchant_short_name(merchant, slug)
        signal = first_present(value(trigger, "payload.title"), value(trigger, "payload.reason"), trigger.get("kind"), default="a new signal")
        offer = active_offer(merchant, category)
        
        if offer:
            if wants_hinglish(merchant):
                offer_text = f" offer '{offer}' use karke"
            else:
                offer_text = f" using {offer}"
        else:
            offer_text = ""
            
        if wants_hinglish(merchant):
            body = f"{name}, maine {merchant_name(merchant)} ke liye {signal} notice kiya hai. Kya main {offer_text} next best WhatsApp message draft karu?"
        else:
            body = f"{name}, I noticed {signal} for {merchant_name(merchant)}. Want me to draft the next best WhatsApp message{offer_text}?"
            
        rationale = "Fallback message uses only trigger and merchant facts and asks for one concrete drafting action."
        return self._message(body, cta_for_action(str(trigger.get("kind", ""))), "vera", trigger, "vera_generic_v1", rationale, name)

    def _compose_customer(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any] | None) -> ComposedMessage:
        customer = customer or {}
        special = ChallengeComposer().compose(category, merchant, trigger, customer)
        if special:
            return special
        kind = str(trigger.get("kind") or "").lower()
        if kind in {"recall_due", "customer_lapsed_soft", "customer_lapsed_hard", "appointment_tomorrow", "chronic_refill_due"}:
            return self._customer_reminder(category, merchant, trigger, customer)
        return self._generic_customer(category, merchant, trigger, customer)

    def _customer_reminder(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any]) -> ComposedMessage:
        cname = first_present(value(customer, "identity.name"), customer.get("name"), default="there")
        mname = merchant_name(merchant)
        short_business = mname.replace("The ", "")
        offer = active_offer(merchant, category)
        last_visit = first_present(value(customer, "relationship.last_visit"), value(trigger, "payload.last_visit"), default=None)
        due = first_present(value(trigger, "payload.due_date"), value(trigger, "payload.runout_date"), value(trigger, "payload.stock_runs_out_iso"), default=None)
        
        if due and "T" in str(due):
            due = str(due).split("T")[0]
            
        slots = first_present(value(trigger, "payload.available_slots"), value(merchant, "availability.available_slots"), default=[])
        slot_text = self._slot_text(slots)
        payload = trigger.get("payload") or {}
        service = str(payload.get("service_due") or "regular visit").replace("_", " ")
        
        relation = f"It's been a while since your last visit" if not last_visit else f"It's been a while since your last visit on {last_visit}"
        if "appointment" in str(trigger.get("kind", "")).lower():
            relation = "This is a reminder for your appointment tomorrow"
        elif "chronic" in str(trigger.get("kind", "")).lower() and due:
            relation = f"Your regular medicines are due on {due}"
        elif "recall" in str(trigger.get("kind", "")).lower():
            relation = f"Your {service} is due"
            if last_visit:
                relation += f" (your last visit was on {last_visit})"
            
        if wants_hinglish(merchant, customer):
            middle = f"{relation}. Aapke liye {slot_text} ready hai." if slot_text else f"{relation}. Hum convenient slot confirm kar denge."
        else:
            middle = f"{relation}. {slot_text} is available." if slot_text else f"{relation}. We will confirm a convenient slot."
            
        offer_text = f" Offer: {offer}." if offer else ""
        body = safe_join([f"Hi {cname}, {short_business} here.", middle, offer_text, "Reply YES to confirm, or STOP to opt out."])
        rationale = "Customer-scoped reminder uses customer identity, merchant attribution, relationship timing, consent-safe CTA, and real offer/slot data when present."
        return self._message(body, "binary_yes_no", "merchant_on_behalf", trigger, "merchant_customer_reminder_v1", rationale, str(cname))

    def _generic_customer(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any]) -> ComposedMessage:
        cname = first_present(value(customer, "identity.name"), default="there")
        mname = merchant_name(merchant)
        reason = first_present(value(trigger, "payload.title"), trigger.get("kind"), default="an update")
        
        if wants_hinglish(merchant, customer):
            body = f"Hi {cname}, {mname} se bol rahe hain. Humare paas aapke liye update hai: {reason}. Reply YES to confirm, or STOP to opt out."
        else:
            body = f"Hi {cname}, {mname} here. We have {reason} for you. Reply YES to confirm, or STOP to opt out."
            
        rationale = "Customer fallback keeps attribution clear and avoids unsupported personalization."
        return self._message(body, "binary_yes_no", "merchant_on_behalf", trigger, "merchant_customer_update_v1", rationale, str(cname))

    def _message(self, body: str, cta: str, send_as: str, trigger: dict[str, Any], template_name: str, rationale: str, lead: str) -> ComposedMessage:
        suppression = first_present(trigger.get("suppression_key"), value(trigger, "payload.suppression_key"), trigger.get("id"), default="unspecified")
        clean_body = body.replace("http://", "").replace("https://", "").strip()
        if len(clean_body) > 315:
            clean_body = clean_body[:315] + "..."
        return ComposedMessage(body=clean_body, cta=cta, send_as=send_as, suppression_key=str(suppression), rationale=rationale, template_name=template_name, template_params=template_params(clean_body, lead))

    def _segment_text(self, segment: Any, merchant: dict[str, Any]) -> str:
        signals = " ".join(str(item).lower() for item in merchant.get("signals", []) or [])
        if segment:
            return f"This maps to your {str(segment).replace('_', ' ')} segment."
        if "high_risk" in signals or "high-risk" in signals:
            return "This maps to your high-risk adult patient cohort."
        return ""

    def _slot_text(self, slots: Any) -> str:
        if isinstance(slots, list) and slots:
            rendered = []
            for slot in slots[:2]:
                if isinstance(slot, dict):
                    rendered.append(first_present(slot.get("label"), slot.get("start"), slot.get("time"), default=""))
                else:
                    rendered.append(str(slot))
            rendered = [item for item in rendered if item]
            if rendered:
                return " or ".join(rendered)
        if isinstance(slots, str) and slots:
            return slots
        return ""
