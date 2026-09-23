from __future__ import annotations

from langchain_core.messages import AIMessage

from models import OrderStatus
from services.llm_service import LLMService, llm_service


def generate_response(state, kind: str = "default") -> str:
    if kind == "unrelated":
        return "I'm Order-Pilot, a restaurant ordering assistant. I can help you place food orders, but I can't assist with general questions."
    if kind == "partial":
        return "We currently have a partial order available. Would you like to proceed with the available items or place a different order?"
    if kind == "clarify":
        return "Please provide the quantity for the item you want."
    if kind == "ambiguous":
        return "I didn't quite understand your response. Please let me know whether you'd like to accept the available items or place a new order."
    if kind == "new_order":
        return "Please provide the new food order you'd like to place."
    if kind == "unavailable":
        return "None of the requested items are available. Please submit a different order."
    if kind == "success":
        return "Your order has been prepared and served successfully. Thank you!"
    if kind == "failure":
        return "I'm sorry, but we weren't able to complete your order after the available attempts. Please try again later."
    if kind == "cook_failure":
        return "I'm sorry, we couldn't prepare your order successfully. We'll try again."
    if kind == "invalid_order":
        return "I couldn't understand that as a complete food order. Please specify the dish and quantity."
    return "Please enter a valid food order."


def response_kind(state) -> str:
    status = state.get("status")
    intent = state.get("intent")
    decision = state.get("partial_order_decision")

    if status == OrderStatus.ORDER_COMPLETED:
        return "success"
    if status == OrderStatus.ORDER_FAILED:
        return "failure"
    if decision == "AMBIGUOUS":
        return "ambiguous"
    if decision == "NEW_ORDER" or state.get("pending_action") == "NEW_ORDER":
        if status == OrderStatus.ORDER_NA:
            return "unavailable"
        return "new_order"
    if status == OrderStatus.ORDER_PARTIAL:
        return "partial"
    if status == OrderStatus.ORDER_NA:
        return "unavailable"
    if intent == "unrelated":
        return "unrelated"
    if intent in {"incomplete_order", "ambiguous"}:
        return "clarify"
    return "default"


def _item_context(state) -> list[dict]:
    items = []
    for item in state.get("order_items", []) or []:
        if hasattr(item, "dish_name"):
            items.append(
                {
                    "dish_name": item.dish_name,
                    "requested_quantity": item.requested_quantity,
                    "available_quantity": getattr(item, "available_quantity", 0),
                    "accepted_quantity": getattr(item, "accepted_quantity", 0),
                }
            )
        elif isinstance(item, dict):
            items.append(item)
    return items


def response_node(state, llm: LLMService | None = None):
    kind = response_kind(state)
    context = {
        "intent": state.get("intent"),
        "status": state.get("status").value
        if hasattr(state.get("status"), "value")
        else state.get("status"),
        "items": _item_context(state),
        "error_message": state.get("error_message"),
        "partial_order_decision": state.get("partial_order_decision"),
    }

    service = llm if llm is not None else llm_service
    if service.available:
        reply = service.generate_response(kind, context)
    else:
        reply = generate_response(state, kind)

    updates: dict = {"messages": [AIMessage(content=reply)]}
    if state.get("status") in {
        OrderStatus.ORDER_COMPLETED,
        OrderStatus.ORDER_FAILED,
        OrderStatus.ORDER_CANCELLED,
    } and not state.get("final_result"):
        success = state.get("status") == OrderStatus.ORDER_COMPLETED
        updates["final_result"] = {
            "success": success,
            "status": state.get("status").value,
        }
    return updates
