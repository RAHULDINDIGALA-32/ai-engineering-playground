from __future__ import annotations

from langgraph.graph import END, StateGraph

from models import OrderStatus
from nodes.cook import cook_node
from nodes.order_confirmation import order_confirmation_node
from nodes.order_parser import semantic_parser_node
from nodes.response import generate_response
from nodes.serve import serve_node
from nodes.user_decision import partial_decision_node
from state import OrderState
from graph.routers import (
    route_after_confirmation,
    route_after_cook,
    route_after_parser,
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


def response_node(state):
    text = state.get("last_user_message") or ""
    if state.get("status") == OrderStatus.ORDER_COMPLETED:
        reply = generate_response(state, "success")
    elif state.get("status") == OrderStatus.ORDER_FAILED:
        reply = generate_response(state, "failure")
    elif state.get("status") == OrderStatus.ORDER_PARTIAL:
        reply = generate_response(state, "partial")
    else:
        reply = generate_response(
            state, "unrelated" if "what is" in text.lower() else "default"
        )
    state["messages"] = state.get("messages", []) + [
        {"role": "assistant", "content": reply}
    ]
    return state


def build_graph():
    workflow = StateGraph(OrderState)
    workflow.add_node("semantic_parser", semantic_parser_node)
    workflow.add_node("confirm_order", order_confirmation_node)
    workflow.add_node("user_decision", partial_decision_node)
    workflow.add_node("cook", cook_node)
    workflow.add_node("serve", serve_node)
    workflow.add_node("response", response_node)
    workflow.add_node("end", lambda state: state)

    workflow.set_entry_point("semantic_parser")
    workflow.add_conditional_edges(
        "semantic_parser",
        route_after_parser,
        {"confirm_order": "confirm_order", "response": "response"},
    )
    workflow.add_conditional_edges(
        "confirm_order",
        route_after_confirmation,
        {"cook": "cook", "user_decision": "user_decision", "response": "response"},
    )
    workflow.add_conditional_edges(
        "user_decision",
        route_after_user_decision,
        {"cook": "cook", "response": "response", "user_decision": "user_decision"},
    )
    workflow.add_conditional_edges(
        "cook",
        route_after_cook,
        {"serve": "serve", "cook": "cook", "response": "response"},
    )
    workflow.add_conditional_edges(
        "serve",
        route_after_serve,
        {"cook": "cook", "serve": "serve", "response": "response"},
    )
    workflow.add_edge("response", END)
    workflow.add_edge("end", END)
    return workflow.compile()


def run_order_agent(initial_input: str, overrides: dict | None = None):
    state = _empty_state()
    if overrides:
        state.update(overrides)
    state["last_user_message"] = initial_input
    graph = build_graph()
    return graph.invoke(state)
