import os
import json
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.models import DecisionType, AuditRecord

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit_log.db")

def clear_db():
    """Helper to clear the SQLite audit database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM audit_records")
        conn.commit()
        print("Audit database logs cleared.")
    except Exception as e:
        print(f"Error clearing database: {e}")
    finally:
        conn.close()

def run_batch():
    # 1. Clear database before starting the batch
    print("Initializing batch run...")
    clear_db()

    # 2. Read generated carts
    carts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "carts.json")
    if not os.path.exists(carts_path):
        print(f"Error: {carts_path} does not exist. Run seed_carts.py first.")
        return

    with open(carts_path, "r") as f:
        carts = json.load(f)

    print(f"Loaded {len(carts)} carts for batch processing.")

    # Initialize FastAPI TestClient
    client = TestClient(app)

    # Stats collectors
    total_propose = 0
    total_decline = 0
    total_baseline_value = 0.0
    total_gained_upsell_value = 0.0
    
    decline_reasons_breakdown = {
        "No rules triggered": 0,
        "Discount conflict": 0,
        "Below confidence threshold": 0
    }
    
    confidence_scores = []

    # 3. Process each cart
    for cart in carts:
        payload = {
            "cart_id": cart["id"],
            "simulate_outcome": cart.get("simulate_outcome")
        }
        
        # Call the endpoint
        response = client.post("/evaluate-cart", json=payload)
        if response.status_code != 200:
            print(f"Error evaluating cart {cart['id']}: {response.text}")
            continue

        record_dict = response.json()
        record = AuditRecord.model_validate(record_dict)

        # Baseline value is the order value of this cart
        total_baseline_value += cart["order_value"]

        # Track decision types
        dec = record.decision
        confidence_scores.append(dec.confidence_score)

        if dec.decision_type == DecisionType.PROPOSE:
            total_propose += 1
            # If customer accepted, add up the upsell value delta
            if record.outcome and record.outcome.accepted:
                total_gained_upsell_value += record.outcome.order_value_delta
        else:
            total_decline += 1
            # Group decline reasons
            reason = dec.reason.lower()
            if "no upsell rules triggered" in reason or "no rule matched" in reason:
                decline_reasons_breakdown["No rules triggered"] += 1
            elif "conflict" in reason or "discount already" in reason:
                decline_reasons_breakdown["Discount conflict"] += 1
            elif "below threshold" in reason or "confidence" in reason:
                decline_reasons_breakdown["Below confidence threshold"] += 1
            else:
                # Fallback if any other custom reasons arise
                decline_reasons_breakdown[dec.reason] = decline_reasons_breakdown.get(dec.reason, 0) + 1

    # 4. Compute aggregate stats
    total_carts = len(carts)
    decline_rate = round((total_decline / total_carts) * 100, 2) if total_carts > 0 else 0.0
    uplift_percentage = round((total_gained_upsell_value / total_baseline_value) * 100, 2) if total_baseline_value > 0 else 0.0

    # Build confidence distribution (grouped by rounded values)
    confidence_distribution = {}
    for score in confidence_scores:
        score_str = f"{score:.2f}"
        confidence_distribution[score_str] = confidence_distribution.get(score_str, 0) + 1

    # Sort distribution keys for readability
    confidence_distribution = dict(sorted(confidence_distribution.items(), key=lambda x: float(x[0])))

    results = {
        "total_carts": total_carts,
        "total_propose": total_propose,
        "total_decline": total_decline,
        "decline_rate_pct": decline_rate,
        "total_baseline_value": round(total_baseline_value, 2),
        "total_gained_upsell_value": round(total_gained_upsell_value, 2),
        "uplift_percentage": uplift_percentage,
        "decline_reasons_breakdown": decline_reasons_breakdown,
        "confidence_score_distribution": confidence_distribution
    }

    # 5. Output results as JSON
    print("\n" + "=" * 50)
    print("BATCH RUN SUMMARY (JSON)")
    print("=" * 50)
    print(json.dumps(results, indent=2))
    print("=" * 50 + "\n")

    # 6. Save results to data/batch_results.json
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {results_path}")

    # 7. Reset/clear database logs before live demo recording starts
    print("Resetting database for the live demo trail...")
    clear_db()

if __name__ == "__main__":
    run_batch()
