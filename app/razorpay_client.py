import os
from typing import Dict, Any, List

# Try importing razorpay. If not installed or fails, we define a fallback structure.
try:
    import razorpay
except ImportError:
    razorpay = None

RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET", "")

client = None
if RAZORPAY_KEY and razorpay:
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
    except Exception:
        pass

MOCK_CARTS: Dict[str, Dict[str, Any]] = {
    "cart_scenario_1": {
        "id": "cart_scenario_1",
        "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
        "order_value": 1200.0,
        "customer_id": "cust_1",
        "has_active_discount": False,
        "purchase_history": [],
        "declined_upsells_count": 0
    },
    "cart_scenario_2": {
        "id": "cart_scenario_2",
        "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
        "order_value": 1200.0,
        "customer_id": "cust_1",
        "has_active_discount": False,
        "purchase_history": [],
        "declined_upsells_count": 0
    },
    "cart_scenario_3": {
        "id": "cart_scenario_3",
        "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
        "order_value": 1200.0,
        "customer_id": "cust_1",
        "has_active_discount": False,
        "purchase_history": [],
        "declined_upsells_count": 0
    },
    "cart_scenario_4": {
        "id": "cart_scenario_4",
        "items": [{"id": "item_C", "price": 500.0, "category": "apparel"}],
        "order_value": 500.0,
        "customer_id": "cust_4",
        "has_active_discount": False,
        "purchase_history": ["apparel"],
        "declined_upsells_count": 2
    },
    "cart_scenario_5": {
        "id": "cart_scenario_5",
        "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
        "order_value": 1200.0,
        "customer_id": "cust_5",
        "has_active_discount": True,
        "purchase_history": [],
        "declined_upsells_count": 0
    }
}

def fetch_cart(cart_id: str) -> Dict[str, Any]:
    """
    Fetches checkout/order from Razorpay test mode if keys are provided.
    Otherwise, falls back to MOCK_CARTS.
    """
    if client:
        try:
            order = client.order.fetch(cart_id)
            # Convert Razorpay Order to cart dictionary
            order_value = order.get("amount", 0) / 100.0  # amount in paise
            notes = order.get("notes", {})
            
            # Read items from note
            items_str = notes.get("items", "")
            items: List[Dict[str, Any]] = []
            for it in items_str.split(","):
                it = it.strip()
                if it:
                    # Support category in note: e.g. "item_A:electronics"
                    if ":" in it:
                        name, cat = it.split(":", 1)
                        items.append({"id": name, "price": 0.0, "category": cat})
                    else:
                        items.append({"id": it, "price": 0.0, "category": ""})
            
            has_active_discount = notes.get("has_active_discount", "false").lower() == "true"
            
            purchase_history_str = notes.get("purchase_history", "")
            purchase_history = [p.strip() for p in purchase_history_str.split(",") if p.strip()]
            
            declined_upsells_count = int(notes.get("declined_upsells_count", "0"))
            
            return {
                "id": order.get("id"),
                "items": items,
                "order_value": order_value,
                "customer_id": notes.get("customer_id", "cust_razorpay"),
                "has_active_discount": has_active_discount,
                "purchase_history": purchase_history,
                "declined_upsells_count": declined_upsells_count
            }
        except Exception:
            pass  # Fail silently and fall back to mock data
            
    # Fallback to mock dictionary
    if cart_id in MOCK_CARTS:
        return MOCK_CARTS[cart_id]
        
    return {
        "id": cart_id,
        "items": [],
        "order_value": 0.0,
        "customer_id": "cust_unknown",
        "has_active_discount": False,
        "purchase_history": [],
        "declined_upsells_count": 0
    }
