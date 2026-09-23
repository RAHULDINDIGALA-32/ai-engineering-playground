from __future__ import annotations

import re

from models import OrderItem, OrderStatus
from services.llm_service import LLMService, llm_service


def decide_partial_order(text: str) -> str:
    if not text:
        return "AMBIGUOUS"

    normalized = text.strip().lower()
    if re.search(
        r"\b(yes|accept|okay|ok|sure|i'll take it|take what you have|proceed)\b",
        normalized,
    ):
        return "ACCEPT_PARTIAL"
    if re.search(
        r"\b(no|reject|new order|different order|something else|not now)\b", normalized
    ):
        return "NEW_ORDER"
    return "AMBIGUOUS"


def _accept_partial_items(order_items: list[OrderItem]) -> list[OrderItem]:
    accepted: list[OrderItem] = []
    for item in order_items:
        accepted_quantity = min(item.requested_quantity, item.available_quantity)
        accepted.append(
            OrderItem(
                dish_name=item.dish_name,
                requested_quantity=item.requested_quantity,
                available_quantity=item.available_quantity,
                accepted_quantity=accepted_quantity,
            )
        )
    return accepted


def partial_decision_node(state, llm: LLMService | None = None):
    if state.get("status") != OrderStatus.ORDER_PARTIAL:
        return {
            "partial_order_decision": None,
            "error_message": "Partial-order decision is not allowed in the current state.",
        }

    text = state.get("last_user_message") or ""
    service = llm if llm is not None else llm_service
    decision = None

    if service.available:
        try:
            decision = service.parse_partial_decision(text)
        except Exception:
            decision = None

    if decision is None:
        decision = decide_partial_order(text)

    if decision == "ACCEPT_PARTIAL":
        items = _accept_partial_items(state.get("order_items") or [])
        cookable = [item for item in items if item.accepted_quantity > 0]
        if not cookable:
            return {
                "partial_order_decision": "ACCEPT_PARTIAL",
                "order_items": items,
                "status": OrderStatus.ORDER_NA,
                "pending_action": "NEW_ORDER",
            }
        return {
            "partial_order_decision": "ACCEPT_PARTIAL",
            "order_items": items,
            "status": OrderStatus.ORDER_CONFIRMED,
            "pending_action": None,
            "clarification_required": False,
        }

    if decision == "NEW_ORDER":
        return {
            "partial_order_decision": "NEW_ORDER",
            "order_items": [],
            "status": None,
            "pending_action": "NEW_ORDER",
            "clarification_required": False,
        }

    return {
        "partial_order_decision": "AMBIGUOUS",
        "clarification_required": True,
        "pending_action": None,
    }
