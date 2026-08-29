import json
import time
from fastapi.testclient import TestClient
from app.main import app
from app.models import DecisionType, AuditRecord
from app.razorpay_client import MOCK_CARTS

client = TestClient(app)

SCENARIOS = [
    {
        "num": 1,
        "name": "Cart missing bundle item, no prior discount",
        "description": "Checks if bundle completion rule proposing a discount is triggered and passes guardrails.",
        "payload": {"cart_id": "cart_scenario_1"}
    },
    {
        "num": 2,
        "name": "Same as #1, simulate customer accepting",
        "description": "Triggers the same rule but simulates an outcome of customer accepting the recommendation.",
        "payload": {
            "cart_id": "cart_scenario_2",
            "simulate_outcome": {
                "accepted": True,
                "order_value_delta": 250.0
            }
        }
    },
    {
        "num": 3,
        "name": "Same as #1, simulate customer declining",
        "description": "Triggers the same rule but simulates an outcome of customer declining the recommendation.",
        "payload": {
            "cart_id": "cart_scenario_3",
            "simulate_outcome": {
                "accepted": False,
                "order_value_delta": 0.0
            }
        }
    },
    {
        "num": 4,
        "name": "Low-value cart, weak rule match",
        "description": "Triggers a rule match but falls below the confidence threshold due to repeated decline penalties.",
        "payload": {"cart_id": "cart_scenario_4"}
    },
    {
        "num": 5,
        "name": "Cart with an active discount already applied",
        "description": "Triggers a high confidence rule, but gets filtered by the conflict guardrail (gated action).",
        "payload": {"cart_id": "cart_scenario_5"}
    }
]

def run_demo():
    print("=" * 80)
    print(" " * 25 + "VETO HACKATHON DEMO RUN")
    print("=" * 80)
    print("Starting bounded upsell-decision evaluation for checkout scenarios...\n")
    
    audit_records = []
    
    for sc in SCENARIOS:
        print(f"--- [Scenario {sc['num']}] {sc['name']} ---")
        print(f"Description: {sc['description']}")
        print(f"Payload sent: {json.dumps(sc['payload'], indent=2)}")
        
        response = client.post("/evaluate-cart", json=sc["payload"])
        if response.status_code != 200:
            print(f"Error: status code {response.status_code}, response: {response.text}")
            continue
            
        record_dict = response.json()
        record = AuditRecord.model_validate(record_dict)
        audit_records.append(record)
        
        print("\nAuditRecord Created (SQLite persisted):")
        print(json.dumps(record_dict, indent=2))
        print("-" * 80 + "\n")
        time.sleep(0.5)

    # Summarize metrics
    total_scenarios = len(audit_records)
    total_declined = sum(1 for r in audit_records if r.decision.decision_type == DecisionType.DECLINE)
    decline_rate = (total_declined / total_scenarios) * 100 if total_scenarios > 0 else 0.0
    
    total_baseline_value = sum(MOCK_CARTS[sc["payload"]["cart_id"]]["order_value"] for sc in SCENARIOS)
    total_uplift_delta = sum(r.outcome.order_value_delta for r in audit_records if r.outcome is not None)
    
    uplift_percentage = (total_uplift_delta / total_baseline_value) * 100 if total_baseline_value > 0 else 0.0
    
    print("=" * 80)
    print(" " * 30 + "DEMO SUMMARY METRICS")
    print("=" * 80)
    print(f"Total Evaluated Checkouts: {total_scenarios}")
    print(f"Declined / Blocked Upsells: {total_declined}")
    print(f"Decline Rate:                {decline_rate:.2f}%")
    print(f"Total Baseline Checkout Value: ${total_baseline_value:.2f}")
    print(f"Total Gained Upsell Value:     ${total_uplift_delta:.2f}")
    print(f"Overall Order Value Uplift %:  {uplift_percentage:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    run_demo()
