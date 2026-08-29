from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    PROPOSE = "PROPOSE"
    DECLINE = "DECLINE"

class ToolCall(BaseModel):
    id: str
    tool_name: str
    cart_id: str
    payload: Dict[str, Any]
    timestamp: str

class Decision(BaseModel):
    id: str
    cart_id: str
    decision_type: DecisionType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    rule_triggered: Optional[str] = None
    timestamp: str

class Outcome(BaseModel):
    id: str
    decision_id: str
    accepted: Optional[bool] = None
    order_value_delta: float = 0.0
    timestamp: str

class AuditRecord(BaseModel):
    id: str
    cart_id: str
    tool_call: Optional[ToolCall] = None
    decision: Decision
    outcome: Optional[Outcome] = None
    timestamp: str
