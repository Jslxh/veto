from fastapi.testclient import TestClient
from app.main import app
from app.models import DecisionType, AuditRecord

client = TestClient(app)

def test_scenario_1_propose_bundle():
    # 1. Cart missing bundle item, no prior discount -> expect PROPOSE, high confidence
    response = client.post("/evaluate-cart", json={"cart_id": "cart_scenario_1"})
    assert response.status_code == 200
    record = AuditRecord.model_validate(response.json())
    assert record.decision.decision_type == DecisionType.PROPOSE
    assert record.decision.rule_triggered == "bundle_completion"
    assert record.decision.confidence_score == 0.8
    assert record.outcome is None

def test_scenario_2_customer_accepts():
    # 2. Same as #1, simulate customer accepting -> Outcome.accepted=True, delta > 0
    response = client.post("/evaluate-cart", json={
        "cart_id": "cart_scenario_2",
        "simulate_outcome": {
            "accepted": True,
            "order_value_delta": 250.0
        }
    })
    assert response.status_code == 200
    record = AuditRecord.model_validate(response.json())
    assert record.decision.decision_type == DecisionType.PROPOSE
    assert record.outcome is not None
    assert record.outcome.accepted is True
    assert record.outcome.order_value_delta == 250.0

def test_scenario_3_customer_declines():
    # 3. Same as #1, simulate customer declining -> Outcome.accepted=False, delta = 0
    response = client.post("/evaluate-cart", json={
        "cart_id": "cart_scenario_3",
        "simulate_outcome": {
            "accepted": False,
            "order_value_delta": 0.0
        }
    })
    assert response.status_code == 200
    record = AuditRecord.model_validate(response.json())
    assert record.decision.decision_type == DecisionType.PROPOSE
    assert record.outcome is not None
    assert record.outcome.accepted is False
    assert record.outcome.order_value_delta == 0.0

def test_scenario_4_weak_rule_match():
    # 4. Low-value cart, weak rule match -> expect DECLINE, reason mentions threshold
    response = client.post("/evaluate-cart", json={"cart_id": "cart_scenario_4"})
    assert response.status_code == 200
    record = AuditRecord.model_validate(response.json())
    assert record.decision.decision_type == DecisionType.DECLINE
    assert "threshold" in record.decision.reason.lower()
    assert record.decision.confidence_score == 0.4

def test_scenario_5_active_discount_conflict():
    # 5. Cart with an active discount already applied -> expect DECLINE, reason mentions conflict
    response = client.post("/evaluate-cart", json={"cart_id": "cart_scenario_5"})
    assert response.status_code == 200
    record = AuditRecord.model_validate(response.json())
    assert record.decision.decision_type == DecisionType.DECLINE
    assert "conflict" in record.decision.reason.lower()
