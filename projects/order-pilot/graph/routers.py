from __future__ import annotations

from models import OrderStatus

TERMINAL_STATUSES = {
    OrderStatus.ORDER_COMPLETED,
    OrderStatus.ORDER_FAILED,
    OrderStatus.ORDER_CANCELLED,
}


def route_from_start(state):
    status = state.get("status")
    pending_action = state.get("pending_action")

    if status in TERMINAL_STATUSES:
        return "response"

    if status == OrderStatus.ORDER_PARTIAL and pending_action != "NEW_ORDER":
        return "user_decision"

    return "semantic_parser"


def route_after_parser(state):
    intent = state.get("intent")
    if intent == "food_order":
        return "confirm_order"
    return "response"


def route_after_confirmation(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_CONFIRMED:
        return "cook"
    if status in {
        OrderStatus.ORDER_PARTIAL,
        OrderStatus.ORDER_NA,
        OrderStatus.ORDER_FAILED,
    }:
        return "response"
    return "response"


def route_after_cook(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_READY:
        return "serve"
    if (
        state.get("last_cook_result") == "FAIL"
        and int(state.get("cook_attempts_remaining", 0)) > 0
        and status != OrderStatus.ORDER_FAILED
    ):
        return "cook"
    return "response"


def route_after_serve(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_COMPLETED:
        return "response"
    if (
        state.get("last_serve_result") == "FAIL"
        and int(state.get("serve_attempts_remaining", 0)) > 0
        and status != OrderStatus.ORDER_FAILED
    ):
        if int(state.get("cook_attempts_remaining", 0)) > 0:
            return "cook"
        return "serve"
    return "response"


def route_after_user_decision(state):
    decision = state.get("partial_order_decision")
    status = state.get("status")
    if decision == "ACCEPT_PARTIAL" and status == OrderStatus.ORDER_CONFIRMED:
        return "cook"
    return "response"
