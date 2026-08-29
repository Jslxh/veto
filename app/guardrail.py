import time
from typing import Optional, Dict, Any
from app.models import Decision, DecisionType

CONFIDENCE_THRESHOLD = 0.65

def has_conflict(cart_data: Dict[str, Any]) -> bool:
    """Helper to check if an active discount already exists on the cart."""
    return cart_data.get("has_active_discount", False) is True

def evaluate_gate(candidate: Optional[Decision], cart_data: Dict[str, Any]) -> Decision:
    """Evaluates the candidate decision against confidence thresholds and conflicts."""
    cart_id = cart_data.get("id", "")
    
    if candidate is None:
        return Decision(
            id="dec_none",
            cart_id=cart_id,
            decision_type=DecisionType.DECLINE,
            confidence_score=0.0,
            reason="No upsell rules triggered",
            rule_triggered=None,
            timestamp=str(time.time())
        )
        
    # Check conflict first
    if has_conflict(cart_data):
        return Decision(
            id=candidate.id,
            cart_id=candidate.cart_id,
            decision_type=DecisionType.DECLINE,
            confidence_score=candidate.confidence_score,
            reason="Conflict: discount already applied to this cart",
            rule_triggered=candidate.rule_triggered,
            timestamp=str(time.time())
        )
        
    # Check confidence threshold
    if candidate.confidence_score < CONFIDENCE_THRESHOLD:
        return Decision(
            id=candidate.id,
            cart_id=candidate.cart_id,
            decision_type=DecisionType.DECLINE,
            confidence_score=candidate.confidence_score,
            reason=f"Confidence {candidate.confidence_score:.2f} below threshold {CONFIDENCE_THRESHOLD}",
            rule_triggered=candidate.rule_triggered,
            timestamp=str(time.time())
        )
        
    # Otherwise, return candidate (which is PROPOSE)
    return candidate
