def test_auto_reply_sequence(client):
    body = {
        "conversation_id": "conv_1",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "Thank you for contacting Dr. Meera's Dental Clinic! Our team will respond shortly.",
        "received_at": "2026-04-26T10:42:00Z",
        "turn_number": 2,
    }
    first = client.post("/v1/reply", json=body).json()
    assert first["action"] == "end"


def test_opt_out_ends(client):
    response = client.post("/v1/reply", json={
        "conversation_id": "conv_2",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "Not interested. Stop messaging me.",
        "received_at": "2026-04-26T10:42:00Z",
        "turn_number": 2,
    })
    assert response.json()["action"] == "end"


def test_intent_transition_sends_action(client):
    response = client.post("/v1/reply", json={
        "conversation_id": "conv_3",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "Ok let's do it. What's next?",
        "received_at": "2026-04-26T10:42:00Z",
        "turn_number": 3,
    })
    data = response.json()
    assert data["action"] == "send"
    assert data["cta"] == "binary_confirm_cancel"


def test_confirmation_returns_draft_for_final_approval(client):
    response = client.post("/v1/reply", json={
        "conversation_id": "conv_5",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "CONFIRM",
        "received_at": "2026-04-26T10:43:00Z",
        "turn_number": 4,
    })
    data = response.json()
    assert data["action"] == "send"
    assert data["cta"] == "binary_send_edit"
    assert data["body"].startswith("Confirmed. Here is the draft")


def test_off_topic_redirects(client):
    response = client.post("/v1/reply", json={
        "conversation_id": "conv_4",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "Can you help me with GST filing?",
        "received_at": "2026-04-26T10:42:00Z",
        "turn_number": 2,
    })
    data = response.json()
    assert data["action"] == "send"
    assert "outside" in data["body"].lower()

def test_repeated_reply_does_not_repeat_body(client):
    body = {
        "conversation_id": "conv_repeat",
        "merchant_id": "m_001",
        "from_role": "merchant",
        "message": "Please explain this",
        "received_at": "2026-04-26T10:42:00Z",
        "turn_number": 2,
    }
    first = client.post("/v1/reply", json=body).json()
    second = client.post("/v1/reply", json={**body, "turn_number": 3}).json()
    assert first["action"] == "send"
    assert second["action"] == "wait"
