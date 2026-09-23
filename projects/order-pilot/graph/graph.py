from __future__ import annotations

from langgraph.graph import END, StateGraph

from ..models import OrderStatus
from ..nodes.cook import cook_node
from ..nodes.order_confirmation import order_confirmation_node
from ..nodes.order_parser import parse_order_input
from ..nodes.serve import serve_node
from ..nodes.user_decision import decide_partial_order
from ..state import OrderState
from .routers import (
    route_after_confirmation,
    route_after_cook,
    route_after_serve,
    route_after_user_decision,
)


def _empty_state() -> OrderState:
    return {
        "messages": [],
        "order_items": [],
        "status": None,
        "partial_order_decision": None,
        "error_message": None,
        "final_result": None,
        "order_attempts_remaining": 3,
        "cook_attempts_remaining": 2,
        "serve_attempts_remaining": 2,
        "last_user_message": None,
    }


def build_graph():
    workflow = StateGraph(OrderState)

    def parse_user_input(state):
        text = state.get("last_user_message") or ""
        parsed = parse_order_input(text)
        state["order_items"] = parsed.get("order_items", [])
        state["status"] = (
            OrderStatus.ORDER_RECEIVED
            if parsed.get("intent") == "food_order"
            else state.get("status")
        )
        return state

    def handle_user_decision(state):
        text = state.get("last_user_message") or ""
        decision = decide_partial_order(text)
        state["partial_order_decision"] = decision
        return state

    workflow.add_node("await_order", parse_user_input)
    workflow.add_node("confirm_order", order_confirmation_node)
    workflow.add_node("user_decision", handle_user_decision)
    workflow.add_node("cook", cook_node)
    workflow.add_node("serve", serve_node)
    workflow.add_node("end", lambda state: state)

    workflow.set_entry_point("await_order")
    workflow.add_conditional_edges(
        "await_order",
        route_after_confirmation,
        {
            "cook": "cook",
            "user_decision": "user_decision",
            "await_order": "await_order",
        },
    )
    workflow.add_conditional_edges(
        "confirm_order",
        route_after_confirmation,
        {
            "cook": "cook",
            "user_decision": "user_decision",
            "await_order": "await_order",
        },
    )
    workflow.add_conditional_edges(
        "user_decision",
        route_after_user_decision,
        {
            "cook": "cook",
            "await_order": "await_order",
            "user_decision": "user_decision",
        },
    )
    workflow.add_conditional_edges(
        "cook", route_after_cook, {"serve": "serve", "cook": "cook", "end": END}
    )
    workflow.add_conditional_edges(
        "serve", route_after_serve, {"cook": "cook", "serve": "serve", "end": END}
    )
    workflow.add_edge("end", END)
    return workflow.compile()


def run_order_agent(initial_input: str, overrides: dict | None = None):
    state = _empty_state()
    if overrides:
        state.update(overrides)
    state["last_user_message"] = initial_input
    graph = build_graph()
    return graph.invoke(state)
