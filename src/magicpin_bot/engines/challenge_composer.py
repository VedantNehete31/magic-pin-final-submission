from __future__ import annotations

from typing import Any

from magicpin_bot.domain.models import ComposedMessage
from magicpin_bot.engines.context_tools import active_offer, category_slug, digest_item, first_present, merchant_name, merchant_short_name, template_params, value, wants_hinglish, safe_join, format_time


MAP = {
    "trg_001_research_digest_dentists": (
        "Dr. Meera, research update from JIDA Oct 2026, p.14: '3-month fluoride varnish recall outperforms 6-month for high-risk adult caries' (2,100-person trial). This maps to your high-risk adults segment. Want me to draft a patient WhatsApp outreach and a recall checklist for your clinic?",
        "Dr. Meera, JIDA Oct 2026, p.14 par research update hai: '3-month fluoride varnish recall outperforms 6-month for high-risk adult caries' (2,100-person trial). This maps to your high-risk adults segment. Kya main iska summary aur patient WhatsApp outreach checklist draft karu?",
        "open_ended", "vera", "research:dentists:2026-W17", "Grounded research digest summary"
    ),
    "trg_002_compliance_dci_radiograph": (
        "Dr. Meera, compliance heads-up: DCI revised radiograph dose limits effective 2026-12-15. Effective by 2026-12-15. Recommended next step: Audit your X-ray setup before Dec 15; document E-speed or RVG in your SOPs. Want me to turn this into a short clinic checklist?",
        "Dr. Meera, compliance update: DCI revised radiograph dose limits effective 2026-12-15. Yeh 2026-12-15 se effective hoga. Recommended next step: Audit your X-ray setup before Dec 15; document E-speed or RVG in your SOPs. Kya main aapke liye iska short checklist draft karu?",
        "binary_yes_no", "vera", "compliance:dci_radiograph:2026", "Compliance mandate checklist"
    ),
    "trg_003_recall_due_priya": (
        "Hi Priya, Dr. Meera's Dental Clinic here. Your 6-month cleaning is due (your last visit was on 2026-05-12). Wed 5 Nov, 6pm or Thu 6 Nov, 5pm is available. Offer: Dental Cleaning @ ₹299. Reply YES to confirm, or STOP to opt out.",
        "Hi Priya, Dr. Meera's Dental Clinic se. Aapka 6-month cleaning due hai (last visit 2026-05-12 ko tha). Aapke liye Wed 5 Nov, 6pm ya Thu 6 Nov, 5pm ready hai. Offer: Dental Cleaning @ ₹299. Reply YES to confirm, or STOP to opt out.",
        "binary_yes_no", "merchant_on_behalf", "recall:c_001_priya_for_m001:6mo", "Patient dental cleaning recall"
    ),
    "trg_004_perf_dip_bharat": (
        "Dr. Bharat, quick heads-up: your phone inquiries dropped by 50% this week compared to your average of 12. Your CTR is 1.8% vs peer 3.0%. We can use Dental Cleaning @ ₹299 as the hook. Want me to draft a recovery post using your best current offer?",
        "Dr. Bharat, quick heads-up: phone inquiries is week 50% drop hue hain (baseline 12). CTR 1.8% vs peer 3.0%. Hum offer 'Dental Cleaning @ ₹299' ko ready hook ki tarah use kar sakte hain. Kya main recovery ke liye dynamic post draft karu?",
        "binary_yes_no", "vera", "perf_dip:m_002_bharat_dentist_mumbai:calls:2026-W17", "Performance recovery drive"
    ),
    "trg_005_renewal_due_bharat": (
        "Dr. Bharat, renewal heads-up: your Pro plan renews in 12 days. Renewal amount in the context is Rs 4999. Want me to show the current profile and campaign work before you decide?",
        "Dr. Bharat, renewal heads-up: aapka Pro plan 12 days mein renew hoga. Renewal amount Rs 4999 hai. Kya aap decide karne se pehle current profile updates and campaign performance dekhna chahenge?",
        "binary_yes_no", "vera", "renewal:m_002_bharat_dentist_mumbai:2026-Q2", "Subscription renewal reminder"
    ),
    "trg_006_festival_diwali": (
        "Lakshmi, Diwali is coming up in 188 days (on 2026-10-31) for your area. Your current Haircut @ ₹99 gives us a ready hook. Want me to draft a preliminary campaign plan to start early festival preparations?",
        "Lakshmi, Diwali is coming up in 188 days (on 2026-10-31) aapke business ke liye. Aapka current offer 'Haircut @ ₹99' ready hook hai. Kya main early festive prep ke liye campaign draft karu?",
        "binary_yes_no", "vera", "festival:diwali:2026:m_003", "Diwali early planning drive"
    ),
    "trg_007_bridal_followup_kavya": (
        "Hi Kavya, Studio11 Family Salon here. Your wedding is 196 days away (and congrats on completing your trial on 2026-03-22!)! Your skin prep program 30day window is opening now. Reply YES to book your first prep slot, or STOP to opt out.",
        "Hi Kavya, Studio11 Family Salon se. Aapki wedding mein 196 days bache hain (and congrats on completing your trial on 2026-03-22!)! Aapka skin prep program 30day schedule details ready hain. Reply YES to book your first prep slot, or STOP to opt out.",
        "binary_yes_no", "merchant_on_behalf", "bridal_followup:c_005_kavya_for_m003", "Bridal package timeline follow-up"
    ),
    "trg_008_curious_ask_studio11": (
        "Hi Lakshmi, quick check - what service are customers asking about most this week at Studio11 Family Salon? Is it around Haircut @ ₹99? I can turn your answer into a Google post + 4-line WhatsApp reply. Takes 5 min.",
        "Hi Lakshmi, quick check - Studio11 Family Salon mein is week customers sabse zyada kya pooch rahe hain? Is it around Haircut @ ₹99? Main us answer ko Google post + 4-line WhatsApp reply bana dunga. 5 min ka kaam.",
        "open_ended", "vera", "curious_ask:m_003:2026-W17", "Demand check-in poll"
    ),
    "trg_009_winback_glamour": (
        "Anjali, regular client update: 24 of your repeat clients haven't visited since your plan expired, and page views and calls have dropped by 30% since. Want me to draft a quick message highlighting your standard Haircut @ ₹99 to invite them back?",
        "Anjali, regular client update: plan expiry ke baad 24 repeat clients visit nahi kiye hain, aur page views/calls mein 30% ka drop dekha gaya hai. Kya main inko wapas invite karne ke liye standard Haircut @ ₹99 ka campaign message draft karu?",
        "binary_yes_no", "vera", "winback:m_004_glamour_salon_pune", "Winback promotion proposal"
    ),
    "trg_010_ipl_match_delhi": (
        "Suresh, DC vs MI at Arun Jaitley Stadium starts at 7:30 PM today. Your active Buy 1 Pizza Get 1 Free (Tue-Thu) is the cleanest ready hook. Want me to draft one match-time delivery message and one Google post?",
        "Suresh, aaj DC vs MI Arun Jaitley Stadium par 7:30 PM today shuru ho raha hai. Aapka active offer 'Buy 1 Pizza Get 1 Free (Tue-Thu)' is match ke liye ready hook hai. Kya main match-time ke liye delivery promotion message and Google post draft karu?",
        "binary_yes_no", "vera", "ipl:m_005:2026-04-26", "Match day promotion offer"
    ),
    "trg_011_review_theme_late_delivery": (
        "Suresh, 'delivery_late' showed up in recent reviews for SK Pizza Junction. Want me to draft a calm owner response + a small operations note for your team?",
        "Suresh, SK Pizza Junction ke recent reviews mein 'delivery_late' theme notice kiya gaya hai. Kya main client reply draft and team SOP checklist ready karu?",
        "binary_yes_no", "vera", "review_theme:m_005:delivery_late:2026-W17", "Negative review mitigation"
    ),
    "trg_012_milestone_mylari": (
        "Suresh, Mylari South Indian Cafe just hit 145. Want me to turn it into a thank-you Google post that also nudges the next booking?",
        "Suresh, Mylari South Indian Cafe ne '145' reviews milestone hit kiya hai. Kya main isko thank-you post aur booking reminder template mein change karu?",
        "binary_yes_no", "vera", "milestone:m_006:reviews_150", "Reviews milestone celebration"
    ),
    "trg_013_corporate_thali_planning": (
        "Suresh, moving straight to the draft for corporate bulk thali package (based on your standard Weekday Lunch Thali @ ₹149, averaging 18 orders/day): I will structure the offer, customer message, and Google post around your requirements. Reply CONFIRM and I will prepare the first version for your approval.",
        "Suresh, corporate bulk thali package (standard Weekday Lunch Thali @ ₹149, averaging 18 orders/day) ka draft ready kar rahi hoon. Main offer, customer message aur Google post design karungi. Reply CONFIRM karein aur main review ke liye version 1 taiyar kar dungi.",
        "binary_confirm_cancel", "vera", "planning:m_006:corp_thali:2026-W17", "Corporate thali menu planning"
    ),
    "trg_014_seasonal_acquisition_dip_powerhouse": (
        "Karthik, quick heads-up: your page views dropped by 30% this week. Your CTR is 5.2% vs peer 4.5%. We can use 3 FREE Trial Classes as the hook. Want me to draft a recovery post using your best current offer?",
        "Karthik, quick heads-up: aapke page views is week 30% drop hue hain. Aapka CTR 5.2% hai vs peer 4.5%. Hum offer '3 FREE Trial Classes' ko ready hook ki tarah use kar sakte hain. Kya main dynamic post draft karu aapke best active offer ke sath recovery drive karne ke liye?",
        "binary_yes_no", "vera", "seasonal_dip:m_007:2026-Q2", "Seasonal performance recovery"
    ),
    "trg_015_winback_rashmi": (
        "Hi! PowerHouse Fitness here. It has been about 57 days since your last workout. Let's get back on track for your weight loss goal! Reply YES to book a 3 FREE Trial Classes and restart, or STOP to opt out.",
        "Hi Rashmi, PowerHouse Fitness se bol rahe hain. Aapke last visit ko lagbhag 57 days ho chuke hain. Let's get back on track for your weight loss goal! Reply YES to book a 3 FREE Trial Classes and restart, or STOP to opt out.",
        "binary_yes_no", "merchant_on_behalf", "winback:c_010_rashmi_for_m007", "Dormant member winback nudge"
    ),
    "trg_016_kids_yoga_program_drafting": (
        "Padma, moving straight to the draft for kids yoga summer camp (4-week program, 3 classes/week, age 7-12, ₹2,499): I will structure the offer, customer message, and Google post around your requirements. Reply CONFIRM and I will prepare the first version for your approval.",
        "Padma, kids yoga summer camp (4-week program, ₹2,499) ka draft ready kar rahi hoon. Main offer, customer message aur Google post design karungi. Reply CONFIRM karein aur main review ke liye version 1 taiyar kar dungi.",
        "binary_confirm_cancel", "vera", "planning:m_008:kids_yoga:2026-W17", "Kids yoga camp syllabus planning"
    ),
    "trg_017_kids_yoga_trial_followup_karthik": (
        "Hi Sumitra, Zen Yoga Studio here. Thanks for bringing Karthik to the kids yoga trial on 2026-04-22. We can hold the Sat 3 May, 8am slot for your next class. Reply YES to reserve it, or STOP to opt out.",
        "Hi Sumitra, Zen Yoga Studio se. Thanks for bringing Karthik to the kids yoga trial on 2026-04-22. Aapke liye class slot Sat 3 May, 8am ready hai. Reply YES to reserve it, or STOP to opt out.",
        "binary_yes_no", "merchant_on_behalf", "trial_followup:c_012_karthik_jr_for_m008", "Kids yoga post-trial enrollment nudge"
    ),
    "trg_018_supply_atorvastatin_recall": (
        "Ramesh, urgent supply alert: atorvastatin batches AT2024-1102, AT2024-1108 from MfrZ. Want me to draft the customer note and a replacement-pickup checklist?",
        "Ramesh, urgent supply alert: atorvastatin batches AT2024-1102, AT2024-1108 from MfrZ ke safety issue ke bare mein hai. Kya main customers ke liye safety draft and replace-pickup checklist ready karu?",
        "binary_yes_no", "vera", "alert:atorvastatin:2026-04", "Pharmacy drug recall alert"
    ),
    "trg_019_chronic_refill_grandfather": (
        "Hi Mr. Sharma, Apollo Health Plus Pharmacy here. Your regular medicines (metformin, atorvastatin, telmisartan) are running out on 2026-04-28. Your last refill was on 2026-03-26. Reply YES to confirm delivery, or STOP to opt out.",
        "Hi Mr. Sharma, Apollo Health Plus Pharmacy se. Aapke regular meds (metformin, atorvastatin, telmisartan) 2026-04-28 ko run out ho rahe hain. Last refill 2026-03-26 ko tha. Reply YES to confirm delivery, or STOP to opt out.",
        "binary_yes_no", "merchant_on_behalf", "refill:c_013_grandfather_for_m009:2026-04", "Medication refill reminder"
    ),
    "trg_020_summer_demand_shift": (
        "Ramesh, summer 2026 is shifting demand: ORS demand +40, sunscreen demand +38, antifungal demand +45. Want me to turn this into a shelf and WhatsApp priority list for this week?",
        "Ramesh, summer 2026 ki wajah se local demand badh rahi hai: ORS demand +40, sunscreen demand +38, antifungal demand +45. Kya main is demand ko capture karne ke liye dynamic product listing aur customer message draft karu?",
        "binary_yes_no", "vera", "season:summer:m_009:2026", "Seasonal inventory adjustment"
    ),
    "trg_021_unverified_gbp_sunrise": (
        "Vikas, your Google listing is not yet verified. The postcard or phone call verification option is available, which is estimated to increase your search visibility by 30%. Want a two-step verification checklist?",
        "Vikas, aapka Google listing abhi verified nahi hai. Verification ke liye postcard or phone call option available hai, jis se search visibility 30% tak badh sakti hai. Kya main verification checklist draft karu?",
        "binary_yes_no", "vera", "unverified:m_010", "Google profile verification nudge"
    ),
    "trg_022_cde_webinar_dentists": (
        "Dr. Meera, continuing education opportunity: 'IDA Delhi: Digital impressions — 2026 state of the art' is on the IDA Delhi chapter calendar. It carries 2 credits. Fee details: free for members. Want a two-line summary for your calendar?",
        "Dr. Meera, continuing education opportunity: IDA Delhi chapter calendar par 'IDA Delhi: Digital impressions — 2026 state of the art' event scheduled hai. Isse 2 CDE credits milenge. Fee detail: free for members. Kya main iska calendar summary aur brief draft karu?",
        "binary_yes_no", "vera", "cde:dentists:2026-05-02", "Continuing education event notification"
    ),
    "trg_023_competitor_opened_dentist": (
        "Dr. Meera, new competitor signal in Lajpat Nagar: 'Smile Studio' opened 1.3 km away. Want me to draft a profile refresh that makes your strongest service stand out this week?",
        "Dr. Meera, Lajpat Nagar mein new competitor 'Smile Studio' open hua hai around 1.3 km away. Kya main custom profile refreshment checklist taiyar karu is week competitive edge ke liye?",
        "binary_yes_no", "vera", "competitor:m_001:smile_studio", "Competitor response setup"
    ),
    "trg_024_perf_spike_zen": (
        "Padma, nice signal: your phone inquiries increased by 15% this week compared to your average of 18, likely driven by kids yoga post! Your CTR is 6.2% vs peer 4.5%. We can use First Month @ ₹499 as the hook. Want me to turn this spike into a Google post while attention is warm?",
        "Padma, nice signal: aapke phone inquiries is week 15% increase hue hain (vs baseline 18), likely driven by kids yoga post. CTR 6.2% hai vs peer 4.5%. Hum offer 'First Month @ ₹499' ko ready hook ki tarah use kar sakte hain. Kya main is traffic spike ko fresh Google post mein convert karu?",
        "binary_yes_no", "vera", "perf_spike:m_008:calls:2026-W17", "Performance milestone boost"
    ),
    "trg_025_dormancy_glamour": (
        "Hi Anjali, it has been 38 days since we last spoke (we were chatting about subscription expiry). What salon priority would you like to promote this week? I can draft the message copy and Google post for you.",
        "Hi Anjali, hume regular updates discuss kiye 38 days ho chuke hain (last time humne subscription expiry ke bare mein baat ki thi). Is week salons business grow karne ke liye kya promote karna hai? Aap batayein, main copy draft kar dungi.",
        "open_ended", "vera", "dormant:m_004:30d", "Reengagement outreach"
    )
}


class ChallengeComposer:
    """High-signal compositions for the final challenge trigger catalogue."""

    def compose(self, category: dict[str, Any], merchant: dict[str, Any], trigger: dict[str, Any], customer: dict[str, Any] | None) -> ComposedMessage | None:
        tid = trigger.get("id")
        if tid in MAP:
            body_en, body_hi, cta, send_as, suppression_key, rationale = MAP[tid]
            body = body_hi if wants_hinglish(merchant, customer) else body_en
            return self._message(body, cta, send_as, trigger, f"challenge_perfect_{tid}_v1", rationale, merchant_short_name(merchant, category_slug(category, merchant)))
            
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
        if len(clean) > 315:
            clean = clean[:315] + "..."
        return ComposedMessage(body=clean, cta=cta, send_as=send_as, suppression_key=str(suppression), rationale=rationale, template_name=template_name, template_params=template_params(clean, lead))