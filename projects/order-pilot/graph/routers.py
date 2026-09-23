from __future__ import annotations

from ..models import OrderStatus


def route_after_confirmation(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_CONFIRMED:
        return "cook"
    if status == OrderStatus.ORDER_PARTIAL:
        return "user_decision"
    if status == OrderStatus.ORDER_NA:
        return "await_order"
    return "await_order"


def route_after_cook(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_READY:
        return "serve"
    if status == OrderStatus.ORDER_FAILED:
        if int(state.get("cook_attempts_remaining", 0)) > 0:
            return "cook"
        return "end"
    return "end"


def route_after_serve(state):
    status = state.get("status")
    if status == OrderStatus.ORDER_COMPLETED:
        return "end"
    if status == OrderStatus.ORDER_FAILED:
        serve_remaining = int(state.get("serve_attempts_remaining", 0))
        if serve_remaining > 0:
            if int(state.get("cook_attempts_remaining", 0)) > 0:
                return "cook"
            return "serve"
        return "end"
    return "end"


def route_after_user_decision(state):
    decision = state.get("partial_order_decision")
    if decision == "ACCEPT_PARTIAL":
        return "cook"
    if decision == "NEW_ORDER":
        return "await_order"
    if decision == "AMBIGUOUS":
        return "user_decision"
    return "await_order"
