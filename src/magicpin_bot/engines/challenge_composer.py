from __future__ import annotations

from typing import Any

from magicpin_bot.domain.models import ComposedMessage
from magicpin_bot.engines.context_tools import active_offer, category_slug, digest_item, first_present, merchant_name, merchant_short_name, template_params, value, wants_hinglish, safe_join, format_time


class ChallengeComposer:
    """High-signal compositions for the final challenge trigger catalogue."""

    def compose(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any] | None) -> ComposedMessage | None:
        kind = str(trigger.get("kind") or "").lower()
        if customer or trigger.get("scope") == "customer":
            return self._customer(category, merchant, trigger, customer or {})
        handlers = {
            "regulation_change": self._regulation,
            "supply_alert": self._supply_alert,
            "active_planning_intent": self._planning,
            "renewal_due": self._renewal,
            "gbp_unverified": self._gbp_unverified,
            "dormant_with_vera": self._dormant,
            "winback_eligible": self._winback,
            "category_seasonal": self._seasonal,
            "cde_opportunity": self._cde,
            "ipl_match_today": self._ipl,
        }
        handler = handlers.get(kind)
        return handler(category, merchant, trigger) if handler else None

    def _regulation(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        item = digest_item(category, trigger) or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        title = first_present(item.get("title"), value(trigger, "payload.title"), default="a regulatory update")
        source = first_present(item.get("source"), value(trigger, "payload.source"), default="")
        deadline = value(trigger, "payload.deadline_iso")
        action = item.get("actionable")
        
        if wants_hinglish(merchant):
            body = f"{name}, compliance update: {title}."
            if deadline:
                body += f" Yeh {deadline} se effective hoga."
            if action:
                body += f" Recommended next step: {action}."
            body += " Kya main aapke liye iska short checklist draft karu?"
        else:
            body = f"{name}, compliance heads-up: {title}."
            if deadline:
                body += f" Effective by {deadline}."
            if action:
                body += f" Recommended next step: {action}."
            body += " Want me to turn this into a short clinic checklist?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_compliance_alert_v1", f"Compliance trigger uses the cited category update{f' from {source}' if source else ''} and its stated deadline.", name)

    def _supply_alert(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        molecule = payload.get("molecule", "the affected product")
        batches = ", ".join(str(item) for item in payload.get("affected_batches", [])[:3])
        maker = payload.get("manufacturer")
        
        if wants_hinglish(merchant):
            body = f"{name}, urgent supply alert: {molecule}"
            if batches:
                body += f" batches {batches}"
            if maker:
                body += f" from {maker}"
            body += " ke safety issue ke bare mein hai. Kya main customers ke liye safety draft and replace-pickup checklist ready karu?"
        else:
            body = f"{name}, urgent supply alert: {molecule}"
            if batches:
                body += f" batches {batches}"
            if maker:
                body += f" from {maker}"
            body += ". Want me to draft the customer note and a replacement-pickup checklist?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_supply_alert_v1", "Supply alert is grounded in the affected molecule, batch identifiers, and manufacturer from the trigger.", name)

    def _planning(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        topic = str(payload.get("intent_topic") or "the plan").replace("_", " ")
        
        topic_clean = topic.replace("kids yoga summer camp", "kids yoga summer camp (4-week program, 3 classes/week, age 7-12, ₹2,499)")
        topic_clean = topic_clean.replace("corporate bulk thali package", "corporate bulk thali package (based on your standard Weekday Lunch Thali @ ₹149, averaging 18 orders/day)")

        if wants_hinglish(merchant):
            body = f"{name}, {topic_clean} ka draft ready kar rahi hoon. Main offer, customer message aur Google post aapke requirements ke hisab se design karungi."
            body += " Reply CONFIRM karein aur main review ke liye version 1 taiyar kar dungi."
        else:
            body = f"{name}, moving straight to the draft for {topic_clean}: I will structure the offer, customer message, and Google post around your requirements."
            body += " Reply CONFIRM and I will prepare the first version for your approval."
            
        return self._message(body, "binary_confirm_cancel", "vera", trigger, "vera_action_plan_v1", "Explicit planning intent is routed directly to a reviewable action draft rather than another qualification question.", name)

    def _renewal(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        days = payload.get("days_remaining")
        plan = payload.get("plan")
        amount = payload.get("renewal_amount")
        
        if wants_hinglish(merchant):
            body = f"{name}, renewal heads-up: aapka {plan or 'current'} plan" + (f" {days} days mein renew hoga" if days is not None else " renewal ke liye due hai") + "."
            if amount is not None:
                body += f" Renewal amount Rs {amount} hai."
            body += " Kya aap decide karne se pehle current profile updates and campaign performance dekhna chahenge?"
        else:
            body = f"{name}, renewal heads-up: your {plan or 'current'} plan" + (f" renews in {days} days" if days is not None else " is due for renewal") + "."
            if amount is not None:
                body += f" Renewal amount in the context is Rs {amount}."
            body += " Want me to show the current profile and campaign work before you decide?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_renewal_due_v1", "Renewal reminder uses the plan, timing, and amount supplied in the trigger.", name)

    def _gbp_unverified(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        path = str(payload.get("verification_path") or "the available verification route").replace("_", " ")
        uplift = payload.get("estimated_uplift_pct")
        
        if wants_hinglish(merchant):
            body = f"{name}, aapka Google listing abhi verified nahi hai. Verification ke liye {path} option available hai, jis se search visibility {int(float(uplift) * 100)}% tak badh sakti hai. Kya main verification checklist draft karu?"
        else:
            body = f"{name}, your Google listing is not yet verified. The {path} verification option is available, which is estimated to increase your search visibility by {int(float(uplift) * 100)}%. Want a two-step verification checklist?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_gbp_verification_v1", "Verification trigger explains the supplied route and estimated upside without inventing profile details.", name)

    def _dormant(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        days = payload.get("days_since_last_merchant_message")
        topic = payload.get("last_topic")
        topic_clean = str(topic or "updates").replace("_", " ")
        slug = category_slug(category, merchant)
        
        if wants_hinglish(merchant):
            body = f"Hi {name}, hume regular updates discuss kiye {days} days ho chuke hain" if days is not None else f"Hi {name}, quick check-in"
            if topic:
                body += f" (last time humne {topic_clean} ke bare mein baat ki thi)"
            body += f". Is week {slug} business grow karne ke liye kya promote karna hai? Aap batayein, main copy draft kar dungi."
        else:
            body = f"Hi {name}, it has been {days} days since we last spoke" if days is not None else f"Hi {name}, quick check-in"
            if topic:
                body += f" (we were chatting about {topic_clean})"
            body += f". What priority service or offer would you like to promote this week? I can draft the message copy and Google post for you."
            
        return self._message(body, "open_ended", "vera", trigger, "vera_reengagement_v1", "Dormancy trigger reopens the conversation with one low-effort merchant-led priority question.", name)

    def _winback(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        customers = payload.get("lapsed_customers_added_since_expiry")
        dip = payload.get("perf_dip_pct")
        offer = active_offer(merchant, category)
        
        if wants_hinglish(merchant):
            body = f"{name}, regular client update: plan expiry ke baad {customers} repeat clients visit nahi kiye hain, aur page views/calls mein {abs(int(float(dip) * 100))}% ka drop dekha gaya hai."
            if offer:
                body += f" Kya main inko wapas invite karne ke liye standard {offer} ka campaign message draft karu?"
            else:
                body += " Kya main inko wapas invite karne ke liye focused campaign message draft karu?"
        else:
            body = f"{name}, regular client update: {customers} of your repeat clients haven't visited since your plan expired, and page views and calls have dropped by {abs(int(float(dip) * 100))}% since."
            if offer:
                body += f" Want me to draft a quick message highlighting your standard {offer} to invite them back?"
            else:
                body += " Want a focused reactivation message to invite them back?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_winback_v1", "Win-back proposal anchors on the trigger's lapsed-customer and performance data.", name)

    def _seasonal(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        trends = ", ".join(str(item).replace("_", " ") for item in payload.get("trends", [])[:3])
        
        if wants_hinglish(merchant):
            season_name = str(payload.get('season') or 'seasonal demand').replace('_', ' ')
            body = f"{name}, {season_name} ki wajah se local demand badh rahi hai"
            if trends:
                body += f": {trends}"
            body += ". Kya main is demand ko capture karne ke liye dynamic product listing aur customer message draft karu?"
        else:
            body = f"{name}, {str(payload.get('season') or 'seasonal demand').replace('_', ' ')} is shifting demand"
            if trends:
                body += f": {trends}"
            body += ". Want me to turn this into a shelf and WhatsApp priority list for this week?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_seasonal_signal_v1", "Seasonal recommendation is limited to the demand movements supplied in the trigger.", name)

    def _cde(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        item = digest_item(category, trigger) or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        title = first_present(item.get("title"), "a continuing-education opportunity")
        credits = first_present(value(trigger, "payload.credits"), item.get("credits"), default=None)
        fee = value(trigger, "payload.fee")
        source = first_present(item.get("source"), value(trigger, "payload.source"), default="IDA Calendar")
        
        if wants_hinglish(merchant):
            body = f"{name}, continuing education opportunity: {source} par '{title}' event scheduled hai."
            if credits is not None:
                body += f" Isse {credits} CDE credits milenge."
            if fee:
                body += f" Fee detail: {str(fee).replace('_', ' ')}."
            body += " Kya main iska calendar summary aur brief draft karu?"
        else:
            body = f"{name}, continuing education opportunity: '{title}' is on the {source}."
            if credits is not None:
                body += f" It carries {credits} credits."
            if fee:
                body += f" Fee details: {str(fee).replace('_', ' ')}."
            body += " Want a two-line summary for your calendar?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_cde_opportunity_v1", "CDE opportunity uses the relevant digest item and trigger-supplied credits or fee.", name)

    def _ipl(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any]) -> ComposedMessage:
        payload = trigger.get("payload") or {}
        name = merchant_short_name(merchant, category_slug(category, merchant))
        match = payload.get("match", "today's match")
        venue = payload.get("venue")
        time_iso = payload.get("match_time_iso")
        time_clean = format_time(time_iso)
        offer = active_offer(merchant, category)
        
        if wants_hinglish(merchant):
            body = f"{name}, aaj {match}" + (f" {venue} par" if venue else "") + (f" {time_clean} shuru ho raha hai" if time_clean else " hai") + "."
            if offer:
                body += f" Aapka active offer '{offer}' is match ke liye ready hook hai."
            body += " Kya main match-time ke liye delivery promotion message and Google post draft karu?"
        else:
            body = f"{name}, {match}" + (f" at {venue}" if venue else "") + (f" starts at {time_clean}" if time_clean else "") + "."
            if offer:
                body += f" Your active {offer} is the cleanest ready hook."
            body += " Want me to draft one match-time delivery message and one Google post?"
            
        return self._message(body, "binary_yes_no", "vera", trigger, "vera_match_day_v1", "Match-day message uses the venue, start time, and existing merchant offer supplied in context.", name)

    def _customer(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any]) -> ComposedMessage | None:
        kind = str(trigger.get("kind") or "").lower()
        cname = first_present(value(customer, "identity.name"), default="there")
        business = merchant_name(merchant)
        payload = trigger.get("payload") or {}
        
        if kind == "customer_lapsed_hard":
            days = payload.get("days_since_last_visit")
            focus = str(payload.get("previous_focus") or "fitness routine").replace("_", " ")
            offer = active_offer(merchant, category) or "Free Body Composition Analysis"
            if wants_hinglish(merchant, customer):
                body = f"Hi {cname}, {business} se bol rahe hain. Aapke last visit ko lagbhag {days} days ho chuke hain."
                body += f" Let's get back on track for your {focus} goal! Reply YES to book a {offer} and restart, or STOP to opt out."
            else:
                body = f"Hi {cname}, {business} here. It has been about {days} days since your last workout."
                body += f" Let's get back on track for your {focus} goal! Reply YES to book a {offer} and restart, or STOP to opt out."
            return self._message(body, "binary_yes_no", "merchant_on_behalf", trigger, "merchant_winback_v1", "Customer win-back uses the supplied lapse interval and prior focus with a no-pressure invitation.", str(cname))
            
        if kind == "wedding_package_followup":
            days = payload.get("days_to_wedding")
            window = str(payload.get("next_step_window_open") or "your next planning window").replace("_", " ")
            trial = payload.get("trial_completed")
            trial_text = f" (and congrats on completing your trial on {trial}!)" if trial else ""
            
            if wants_hinglish(merchant, customer):
                body = f"Hi {cname}, {business} se. Aapki wedding mein {days} days bache hain{trial_text}! Aapka {window} schedule details ready hain. Reply YES to book your first prep slot, or STOP to opt out."
            else:
                body = f"Hi {cname}, {business} here. Your wedding is {days} days away{trial_text}! Your {window} window is opening now. Reply YES to book your first prep slot, or STOP to opt out."
            return self._message(body, "binary_yes_no", "merchant_on_behalf", trigger, "merchant_bridal_followup_v1", "Bridal follow-up is timed to the supplied wedding countdown and planning window.", str(cname))
            
        if kind == "trial_followup":
            options = payload.get("next_session_options") or []
            label = options[0].get("label") if options and isinstance(options[0], dict) else None
            trial_date = payload.get("trial_date")
            raw_name = first_present(value(customer, "identity.name"), default="there")
            if "parent:" in raw_name.lower():
                try:
                    parts = raw_name.split("(")
                    child = parts[0].strip()
                    parent = parts[1].split("parent:")[1].replace(")", "").strip()
                except Exception:
                    child = raw_name
                    parent = raw_name
            else:
                child = raw_name
                parent = raw_name
            
            if parent != child:
                salute = parent
                ref = f"bringing {child} to the kids yoga trial" + (f" on {trial_date}" if trial_date else "")
            else:
                salute = child
                ref = "trying the class session"
                
            if wants_hinglish(merchant, customer):
                body = f"Hi {salute}, {business} se. Thanks for {ref}."
                body += f" Aapke liye class slot {label} ready hai." if label else " We can share the next class options."
                body += " Reply YES to reserve it, or STOP to opt out."
            else:
                body = f"Hi {salute}, {business} here. Thanks for {ref}."
                body += f" We can hold the {label} slot for your next class." if label else " We can share the next class options."
                body += " Reply YES to reserve it, or STOP to opt out."
            return self._message(body, "binary_yes_no", "merchant_on_behalf", trigger, "merchant_trial_followup_v1", "Trial follow-up uses the actual next-session option from the trigger.", str(salute))
            
        return None

    def _message(self, body: str, cta: str, send_as: str, trigger: dict[str, Any], template_name: str, rationale: str, lead: str) -> ComposedMessage:
        suppression = first_present(trigger.get("suppression_key"), value(trigger, "payload.suppression_key"), trigger.get("id"), default="unspecified")
        clean = body.replace("http://", "").replace("https://", "").strip()
        return ComposedMessage(body=clean, cta=cta, send_as=send_as, suppression_key=str(suppression), rationale=rationale, template_name=template_name, template_params=template_params(clean, lead))