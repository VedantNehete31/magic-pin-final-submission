import pytest
from fastapi.testclient import TestClient

from magicpin_bot.api.app import app
from magicpin_bot.services.context_store import store


@pytest.fixture
def client():
    store.reset()
    with TestClient(app) as test_client:
        yield test_client
    store.reset()


@pytest.fixture
def sample_contexts():
    category = {
        "slug": "dentists",
        "offer_catalog": [{"title": "Dental Cleaning @ Rs 299", "status": "active"}],
        "voice": {"tone": "peer_clinical"},
        "peer_stats": {"avg_ctr": 0.03},
        "digest": [{
            "id": "d_1",
            "title": "3-month fluoride recall cuts caries recurrence 38% better than 6-month",
            "source": "JIDA Oct 2026, p.14",
            "trial_n": 2100,
            "patient_segment": "high_risk_adults",
        }],
    }
    merchant = {
        "merchant_id": "m_001",
        "category_slug": "dentists",
        "identity": {
            "name": "Dr. Meera's Dental Clinic",
            "owner_first_name": "Meera",
            "city": "Delhi",
            "locality": "Lajpat Nagar",
            "languages": ["en", "hi"],
        },
        "performance": {"views": 2410, "calls": 18, "directions": 45, "ctr": 0.021, "delta_7d": {"views_pct": 0.18}},
        "offers": [{"title": "Dental Cleaning @ Rs 299", "status": "active"}],
        "signals": ["high_risk_adult_cohort", "ctr_below_peer_median"],
    }
    trigger = {
        "id": "trg_001",
        "scope": "merchant",
        "kind": "research_digest",
        "source": "external",
        "merchant_id": "m_001",
        "payload": {"category": "dentists", "top_item_id": "d_1"},
        "urgency": 2,
        "suppression_key": "research:dentists:2026-W17",
        "expires_at": "2026-05-03T00:00:00Z",
    }
    customer = {
        "customer_id": "c_001",
        "merchant_id": "m_001",
        "identity": {"name": "Priya", "language_pref": "hi-en mix"},
        "relationship": {"last_visit": "2026-05-12"},
        "preferences": {"preferred_slots": "weekday_evening"},
        "consent": {"scope": ["recall_reminders"]},
    }
    customer_trigger = {
        "id": "trg_002",
        "scope": "customer",
        "kind": "recall_due",
        "source": "internal",
        "merchant_id": "m_001",
        "customer_id": "c_001",
        "payload": {"available_slots": ["Wed 5 Nov, 6pm", "Thu 6 Nov, 5pm"]},
        "urgency": 3,
        "suppression_key": "recall:c_001:6mo",
        "expires_at": "2026-12-01T00:00:00Z",
    }
    return category, merchant, trigger, customer, customer_trigger


def push(client, scope, context_id, payload, version=1):
    return client.post("/v1/context", json={
        "scope": scope,
        "context_id": context_id,
        "version": version,
        "payload": payload,
        "delivered_at": "2026-04-26T10:00:00Z",
    })

