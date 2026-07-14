from conftest import push


def test_healthz_and_metadata(client):
    health = client.get("/v1/healthz")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    metadata = client.get("/v1/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["model"] == "vedant-deterministic-composer-v1"


def test_context_versioning(client, sample_contexts):
    category, _, _, _, _ = sample_contexts
    first = push(client, "category", "dentists", category, 1)
    assert first.json()["accepted"] is True
    replay = push(client, "category", "dentists", category, 1)
    assert replay.status_code == 200
    assert replay.json()["accepted"] is True
    newer = push(client, "category", "dentists", {**category, "peer_stats": {"avg_ctr": 0.04}}, 2)
    assert newer.json()["accepted"] is True
    stale = push(client, "category", "dentists", category, 1)
    assert stale.status_code == 409
    assert stale.json()["detail"] == {"accepted": False, "reason": "stale_version", "current_version": 2}


def test_tick_composes_merchant_action(client, sample_contexts):
    category, merchant, trigger, _, _ = sample_contexts
    push(client, "category", "dentists", category)
    push(client, "merchant", "m_001", merchant)
    push(client, "trigger", "trg_001", trigger)
    response = client.post("/v1/tick", json={"now": "2026-04-26T10:35:00Z", "available_triggers": ["trg_001"]})
    assert response.status_code == 200
    actions = response.json()["actions"]
    assert len(actions) == 1
    assert actions[0]["send_as"] == "vera"
    assert actions[0]["template_name"] == "vera_research_digest_v1"
    assert "JIDA Oct 2026" in actions[0]["body"]
    assert actions[0]["suppression_key"] == "research:dentists:2026-W17"


def test_tick_composes_customer_action(client, sample_contexts):
    category, merchant, _, customer, customer_trigger = sample_contexts
    push(client, "category", "dentists", category)
    push(client, "merchant", "m_001", merchant)
    push(client, "customer", "c_001", customer)
    push(client, "trigger", "trg_002", customer_trigger)
    response = client.post("/v1/tick", json={"now": "2026-04-26T11:00:00Z", "available_triggers": ["trg_002"]})
    action = response.json()["actions"][0]
    assert action["send_as"] == "merchant_on_behalf"
    assert action["customer_id"] == "c_001"
    assert "Priya" in action["body"]
    assert "Wed 5 Nov" in action["body"]


def test_suppression_prevents_duplicate_send(client, sample_contexts):
    category, merchant, trigger, _, _ = sample_contexts
    push(client, "category", "dentists", category)
    push(client, "merchant", "m_001", merchant)
    push(client, "trigger", "trg_001", trigger)
    first = client.post("/v1/tick", json={"now": "2026-04-26T10:35:00Z", "available_triggers": ["trg_001"]})
    second = client.post("/v1/tick", json={"now": "2026-04-26T10:40:00Z", "available_triggers": ["trg_001"]})
    assert len(first.json()["actions"]) == 1
    assert second.json()["actions"] == []

def test_tick_skips_customer_without_consent(client, sample_contexts):
    category, merchant, _, customer, customer_trigger = sample_contexts
    no_consent_customer = {**customer, "consent": {"scope": []}}
    push(client, "category", "dentists", category)
    push(client, "merchant", "m_001", merchant)
    push(client, "customer", "c_001", no_consent_customer)
    push(client, "trigger", "trg_002", customer_trigger)
    response = client.post("/v1/tick", json={"now": "2026-04-26T11:00:00Z", "available_triggers": ["trg_002"]})
    assert response.json()["actions"] == []

def test_tick_skips_customer_without_matching_consent_scope(client, sample_contexts):
    category, merchant, _, customer, customer_trigger = sample_contexts
    wrong_scope_customer = {**customer, "consent": {"scope": ["appointment_reminders"]}}
    push(client, "category", "dentists", category)
    push(client, "merchant", "m_001", merchant)
    push(client, "customer", "c_001", wrong_scope_customer)
    push(client, "trigger", "trg_002", customer_trigger)
    response = client.post("/v1/tick", json={"now": "2026-04-26T11:00:00Z", "available_triggers": ["trg_002"]})
    assert response.json()["actions"] == []
