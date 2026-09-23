from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from nodes.cook import CookSimulator, cook_node
from nodes.order_confirmation import order_confirmation_node
from nodes.order_parser import semantic_parser_node
from nodes.response import response_node as default_response_node
from nodes.serve import ServeSimulator, serve_node
from nodes.user_decision import partial_decision_node
from services.llm_service import LLMService, llm_service
from state import OrderState
from graph.routers import (
    route_after_confirmation,
    route_after_cook,
    route_after_parser,
    route_after_serve,
    route_after_user_decision,
    route_from_start,
)


def empty_state() -> OrderState:
    return {
        "messages": [],
        "session_id": "sess-default",
        "intent": None,
        "order_items": [],
        "status": None,
        "partial_order_decision": None,
        "error_message": None,
        "final_result": None,
        "order_attempts_remaining": 3,
        "cook_attempts_remaining": 2,
        "serve_attempts_remaining": 2,
        "last_user_message": None,
        "clarification_required": False,
        "pending_action": None,
        "last_operation_id": None,
        "last_cook_result": None,
        "last_serve_result": None,
    }


def build_graph(
    *,
    cook_simulator: CookSimulator | None = None,
    serve_simulator: ServeSimulator | None = None,
    llm: LLMService | None = None,
    checkpointer=None,
):
    service = llm if llm is not None else llm_service

    def semantic_parser(state):
        return semantic_parser_node(state, llm=service)

    def confirm_order(state):
        return order_confirmation_node(state)

    def user_decision(state):
        return partial_decision_node(state, llm=service)

    def cook(state):
        return cook_node(state, cook_simulator)

    def serve(state):
        return serve_node(state, serve_simulator)

    def response(state):
        return default_response_node(state, llm=service)

    workflow = StateGraph(OrderState)
    workflow.add_node("semantic_parser", semantic_parser)
    workflow.add_node("confirm_order", confirm_order)
    workflow.add_node("user_decision", user_decision)
    workflow.add_node("cook", cook)
    workflow.add_node("serve", serve)
    workflow.add_node("response", response)

    workflow.add_conditional_edges(
        START,
        route_from_start,
        {
            "semantic_parser": "semantic_parser",
            "user_decision": "user_decision",
            "response": "response",
        },
    )
    workflow.add_conditional_edges(
        "semantic_parser",
        route_after_parser,
        {"confirm_order": "confirm_order", "response": "response"},
    )
    workflow.add_conditional_edges(
        "confirm_order",
        route_after_confirmation,
        {"cook": "cook", "response": "response"},
    )
    workflow.add_conditional_edges(
        "user_decision",
        route_after_user_decision,
        {"cook": "cook", "response": "response"},
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
    return workflow.compile(checkpointer=checkpointer)


def run_order_agent(initial_input: str, overrides: dict | None = None):
    state = empty_state()
    if overrides:
        state.update(overrides)
    state["last_user_message"] = initial_input
    graph = build_graph()
    return graph.invoke(state, {"recursion_limit": 25})
