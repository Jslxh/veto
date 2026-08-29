import uuid
import time
from typing import Dict, Any, Optional
from app.models import Decision, DecisionType

def calculate_penalty(cart_data: Dict[str, Any]) -> float:
    # Check if customer has declined a similar upsell twice already in the mock history
    declined_count = cart_data.get("declined_upsells_count", 0)
    if declined_count >= 2:
        return -0.3
    return 0.0

def bundle_completion(cart_data: Dict[str, Any]) -> Optional[Decision]:
    items = cart_data.get("items", [])
    item_ids = [item.get("id") for item in items]
    order_value = cart_data.get("order_value", 0.0)
    
    # Check: cart has item A ("item_A"), missing item B ("item_B"), order value >= 1000
    has_a = "item_A" in item_ids
    has_b = "item_B" in item_ids
    
    if has_a and not has_b and order_value >= 1000:
        base_confidence = 0.8
        penalty = calculate_penalty(cart_data)
        confidence = round(max(0.0, base_confidence + penalty), 2)
        
        reason = f"Cart has item_A, missing item_B, order value >= 1000"
        return Decision(
            id=f"dec_{uuid.uuid4().hex[:8]}",
            cart_id=cart_data.get("id", ""),
            decision_type=DecisionType.PROPOSE,
            confidence_score=confidence,
            reason=reason,
            rule_triggered="bundle_completion",
            timestamp=str(time.time())
        )
    return None

def high_value_threshold(cart_data: Dict[str, Any]) -> Optional[Decision]:
    order_value = cart_data.get("order_value", 0.0)
    if order_value >= 5000:
        base_confidence = 0.75
        penalty = calculate_penalty(cart_data)
        confidence = round(max(0.0, base_confidence + penalty), 2)
        
        reason = f"Order value >= 5000"
        return Decision(
            id=f"dec_{uuid.uuid4().hex[:8]}",
            cart_id=cart_data.get("id", ""),
            decision_type=DecisionType.PROPOSE,
            confidence_score=confidence,
            reason=reason,
            rule_triggered="high_value_threshold",
            timestamp=str(time.time())
        )
    return None

def repeat_customer_affinity(cart_data: Dict[str, Any]) -> Optional[Decision]:
    purchase_history = cart_data.get("purchase_history", [])
    items = cart_data.get("items", [])
    cart_categories = {item.get("category") for item in items if item.get("category")}
    
    # Check if customer has purchase history in same category as any item currently in the cart
    has_category_match = any(cat in purchase_history for cat in cart_categories)
    
    if has_category_match:
        base_confidence = 0.7
        penalty = calculate_penalty(cart_data)
        confidence = round(max(0.0, base_confidence + penalty), 2)
        
        reason = f"Customer has purchase history in same category"
        return Decision(
            id=f"dec_{uuid.uuid4().hex[:8]}",
            cart_id=cart_data.get("id", ""),
            decision_type=DecisionType.PROPOSE,
            confidence_score=confidence,
            reason=reason,
            rule_triggered="repeat_customer_affinity",
            timestamp=str(time.time())
        )
    return None
