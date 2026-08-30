import uuid
import time
from typing import TypedDict, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from app.models import ToolCall, Decision, Outcome, AuditRecord, DecisionType
from app.rules import bundle_completion, high_value_threshold, repeat_customer_affinity
from app.guardrail import evaluate_gate
from app.razorpay_client import fetch_cart
from app.audit_log import save_record, get_all_records

# Define the LangGraph State
class AgentState(TypedDict):
    cart_id: str
    simulate_outcome: Optional[Dict[str, Any]]
    cart_data: Optional[Dict[str, Any]]
    tool_call: Optional[ToolCall]
    candidate_decision: Optional[Decision]
    decision: Optional[Decision]
    outcome: Optional[Outcome]
    audit_record: Optional[AuditRecord]

# Node 1: Fetch checkout/cart data
def fetch_cart_node(state: AgentState) -> Dict[str, Any]:
    cart_id = state["cart_id"]
    
    # Generate ToolCall log
    tool_call = ToolCall(
        id=f"tc_{uuid.uuid4().hex[:8]}",
        tool_name="razorpay_fetch_cart",
        cart_id=cart_id,
        payload={"cart_id": cart_id},
        timestamp=str(time.time())
    )
    
    cart_data = fetch_cart(cart_id)
    
    return {
        "cart_data": cart_data,
        "tool_call": tool_call
    }

# Node 2: Evaluate upsell rules
def evaluate_rules_node(state: AgentState) -> Dict[str, Any]:
    cart_data = state["cart_data"]
    if not cart_data:
        return {"candidate_decision": None}
        
    # Run the three rules
    candidates = []
    
    decision_bundle = bundle_completion(cart_data)
    if decision_bundle:
        candidates.append(decision_bundle)
        
    decision_high_val = high_value_threshold(cart_data)
    if decision_high_val:
        candidates.append(decision_high_val)
        
    decision_affinity = repeat_customer_affinity(cart_data)
    if decision_affinity:
        candidates.append(decision_affinity)
        
    # Choose candidate with the highest confidence score
    candidate_decision = None
    if candidates:
        candidate_decision = max(candidates, key=lambda d: d.confidence_score)
        
    return {"candidate_decision": candidate_decision}

# Node 3: Apply guardrail gate
def apply_guardrail_node(state: AgentState) -> Dict[str, Any]:
    candidate_decision = state["candidate_decision"]
    cart_data = state["cart_data"] or {}
    
    decision = evaluate_gate(candidate_decision, cart_data)
    return {"decision": decision}

# Node 4: Process outcome simulation
def process_outcome_node(state: AgentState) -> Dict[str, Any]:
    decision = state["decision"]
    simulate_outcome = state["simulate_outcome"]
    
    outcome = None
    if decision and decision.decision_type == DecisionType.PROPOSE and simulate_outcome:
        accepted = simulate_outcome.get("accepted")
        # delta is only applied if accepted is True
        delta = simulate_outcome.get("order_value_delta", 0.0) if accepted else 0.0
        
        outcome = Outcome(
            id=f"out_{uuid.uuid4().hex[:8]}",
            decision_id=decision.id,
            accepted=accepted,
            order_value_delta=delta,
            timestamp=str(time.time())
        )
        
    return {"outcome": outcome}

# Node 5: Save audit log record
def save_audit_node(state: AgentState) -> Dict[str, Any]:
    cart_id = state["cart_id"]
    tool_call = state["tool_call"]
    decision = state["decision"]
    outcome = state["outcome"]
    
    assert decision is not None, "Decision cannot be None in save_audit node"
    
    audit_record = AuditRecord(
        id=f"audit_{uuid.uuid4().hex[:8]}",
        cart_id=cart_id,
        tool_call=tool_call,
        decision=decision,
        outcome=outcome,
        timestamp=str(time.time())
    )
    
    save_record(audit_record)
    return {"audit_record": audit_record}

# Build LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("fetch_cart", fetch_cart_node)
workflow.add_node("evaluate_rules", evaluate_rules_node)
workflow.add_node("apply_guardrail", apply_guardrail_node)
workflow.add_node("process_outcome", process_outcome_node)
workflow.add_node("save_audit", save_audit_node)

workflow.set_entry_point("fetch_cart")
workflow.add_edge("fetch_cart", "evaluate_rules")
workflow.add_edge("evaluate_rules", "apply_guardrail")
workflow.add_edge("apply_guardrail", "process_outcome")
workflow.add_edge("process_outcome", "save_audit")
workflow.add_edge("save_audit", END)

app_graph = workflow.compile()

# FastAPI application
app = FastAPI(title="VETO Bounded Upsell-Decision Agent")

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

class EvaluateCartRequest(BaseModel):
    cart_id: str
    simulate_outcome: Optional[Dict[str, Any]] = None

@app.post("/evaluate-cart", response_model=AuditRecord)
def evaluate_cart(request: EvaluateCartRequest):
    try:
        initial_state = {
            "cart_id": request.cart_id,
            "simulate_outcome": request.simulate_outcome,
            "cart_data": None,
            "tool_call": None,
            "candidate_decision": None,
            "decision": None,
            "outcome": None,
            "audit_record": None
        }
        
        result = app_graph.invoke(initial_state)
        audit_record = result.get("audit_record")
        if not audit_record:
            raise HTTPException(status_code=500, detail="Failed to produce audit record")
            
        return audit_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit-records")
def get_audit_records():
    return get_all_records()
