from langchain_core.messages import AIMessage
import pytest

from graph.graph import build_graph, empty_state
from graph.routers import (
    route_after_confirmation,
    route_after_cook,
    route_after_serve,
    route_after_user_decision,
    route_from_start,
)
from models import OrderItem, OrderStatus
from nodes.cook import CookSimulator, cook_order
from nodes.order_confirmation import confirm_order
from nodes.order_parser import parse_order_input, semantic_parser_node
from nodes.response import response_node
from nodes.serve import ServeSimulator
from nodes.user_decision import decide_partial_order, partial_decision_node
from services.menu_service import get_available_quantity


class UnavailableLLM:
    available = False


@pytest.mark.parametrize(
    "text, expected",
    [
        ("I want 2 burgers and 1 pizza", [("burger", 2), ("pizza", 1)]),
        ("Can I get 3 biryani?", [("biryani", 3)]),
        (
            "our order: 50 burgers, 25 cokes & 25 biryanis",
            [("burger", 50), ("coke", 25), ("biryani", 25)],
        ),
    ],
)
def test_order_parser_extracts_items(text, expected):
    parsed = parse_order_input(text)
    assert parsed["intent"] == "food_order"
    assert [
        (item["dish_name"], item["requested_quantity"])
        for item in parsed["order_items"]
    ] == expected


def test_order_parser_unrelated_input():
    parsed = parse_order_input("What is the capital of France?")
    assert parsed["intent"] == "unrelated"
    assert parsed["order_items"] == []


def test_order_parser_missing_quantity():
    parsed = parse_order_input("I want pizza.")
    assert parsed["intent"] == "incomplete_order"


def test_semantic_parser_sets_intent_and_items():
    state = {"last_user_message": "I want 2 burgers and 1 pizza"}
    updated = semantic_parser_node(state, llm=UnavailableLLM())
    assert updated["intent"] == "food_order"
    assert updated["status"] == OrderStatus.ORDER_RECEIVED
    assert len(updated["order_items"]) == 2
    assert isinstance(updated["order_items"][0], OrderItem)


def test_semantic_parser_does_not_mutate_status_for_unrelated():
    updated = semantic_parser_node(
        {"last_user_message": "What is the capital of France?"},
        llm=UnavailableLLM(),
    )
    assert updated["intent"] == "unrelated"
    assert "status" not in updated
    assert "order_items" not in updated


def test_response_node_creates_assistant_message():
    state = {
        "last_user_message": "I want 2 burgers",
        "status": OrderStatus.ORDER_PARTIAL,
        "messages": [],
        "order_items": [],
    }
    updated = response_node(state, llm=UnavailableLLM())
    last_message = updated["messages"][-1]
    assert isinstance(last_message, AIMessage)
    assert "partial" in last_message.content.lower()


def test_response_node_uses_llm_service_when_available():
    class FakeLLM:
        available = True

        def generate_response(self, kind, context):
            assert kind == "partial"
            return "We have 5 burgers available, but you asked for 66. Proceed with 5?"

    updated = response_node(
        {
            "status": OrderStatus.ORDER_PARTIAL,
            "messages": [],
            "order_items": [],
        },
        llm=FakeLLM(),
    )
    assert (
        updated["messages"][-1].content
        == "We have 5 burgers available, but you asked for 66. Proceed with 5?"
    )


def test_order_confirmation_fully_available():
    order_items = [
        OrderItem(
            dish_name="burger",
            requested_quantity=2,
            available_quantity=0,
            accepted_quantity=0,
        )
    ]
    result = confirm_order(order_items)
    assert result["status"] == OrderStatus.ORDER_CONFIRMED
    assert result["order_items"][0]["available_quantity"] == 5
    assert result["order_items"][0]["accepted_quantity"] == 2


def test_order_confirmation_partial():
    order_items = [
        OrderItem(
            dish_name="burger",
            requested_quantity=7,
            available_quantity=0,
            accepted_quantity=0,
        ),
        OrderItem(
            dish_name="pizza",
            requested_quantity=2,
            available_quantity=0,
            accepted_quantity=0,
        ),
    ]
    result = confirm_order(order_items)
    assert result["status"] == OrderStatus.ORDER_PARTIAL
    assert result["order_items"][0]["available_quantity"] == 5
    assert result["order_items"][1]["available_quantity"] == 5


def test_user_decision_accept_partial():
    decision = decide_partial_order("Yes, I'll take what you have.")
    assert decision == "ACCEPT_PARTIAL"


def test_user_decision_ambiguous():
    decision = decide_partial_order("Maybe")
    assert decision == "AMBIGUOUS"


def test_partial_decision_requires_partial_status():
    updated = partial_decision_node(
        {
            "status": OrderStatus.ORDER_COMPLETED,
            "last_user_message": "yes",
            "order_items": [],
        },
        llm=UnavailableLLM(),
    )
    assert updated["partial_order_decision"] is None


def test_menu_lookup():
    assert get_available_quantity("pizza") == 5
    assert get_available_quantity("dragon burger") == 0


def test_cook_simulator_deterministic_sequence():
    sim = CookSimulator(["FAIL", "SUCCESS"])
    assert sim.run() == "FAIL"
    assert sim.run() == "SUCCESS"


def test_serve_simulator_deterministic_sequence():
    sim = ServeSimulator(["FAIL", "SUCCESS"])
    assert sim.run() == "FAIL"
    assert sim.run() == "SUCCESS"


def test_cook_failure_does_not_fail_order_while_retries_remain():
    result = cook_order(
        {"cook_attempts_remaining": 2, "session_id": "s"},
        CookSimulator(["FAIL"]),
    )
    assert result["status"] == OrderStatus.ORDER_COOKING
    assert result["cook_attempts_remaining"] == 1
    assert result["last_cook_result"] == "FAIL"
    assert "final_result" not in result


def test_route_partial_confirmation_waits_for_user():
    assert (
        route_after_confirmation({"status": OrderStatus.ORDER_PARTIAL}) == "response"
    )


def test_route_ambiguous_decision_does_not_loop():
    assert (
        route_after_user_decision(
            {
                "partial_order_decision": "AMBIGUOUS",
                "status": OrderStatus.ORDER_PARTIAL,
            }
        )
        == "response"
    )


def test_route_from_start_uses_user_decision_for_partial():
    assert (
        route_from_start({"status": OrderStatus.ORDER_PARTIAL}) == "user_decision"
    )
    assert route_from_start({"status": None}) == "semantic_parser"


def test_route_after_serve_skips_cook_when_cook_exhausted():
    assert (
        route_after_serve(
            {
                "status": OrderStatus.ORDER_SERVING,
                "last_serve_result": "FAIL",
                "serve_attempts_remaining": 1,
                "cook_attempts_remaining": 0,
            }
        )
        == "serve"
    )


def test_route_after_cook_retries_then_serves():
    assert (
        route_after_cook(
            {
                "status": OrderStatus.ORDER_COOKING,
                "last_cook_result": "FAIL",
                "cook_attempts_remaining": 1,
            }
        )
        == "cook"
    )
    assert route_after_cook({"status": OrderStatus.ORDER_READY}) == "serve"


def test_partial_order_does_not_recurse():
    graph = build_graph(llm=UnavailableLLM())
    state = empty_state()
    state["last_user_message"] = "our order: 50 burgers, 25 cokes & 25 biryanis"
    result = graph.invoke(state, {"recursion_limit": 25})
    assert result["status"] == OrderStatus.ORDER_PARTIAL
    assert result["order_attempts_remaining"] == 2
    assert isinstance(result["messages"][-1], AIMessage)


def test_accept_partial_then_complete():
    graph = build_graph(
        llm=UnavailableLLM(),
        cook_simulator=CookSimulator(["SUCCESS"]),
        serve_simulator=ServeSimulator(["SUCCESS"]),
    )
    state = empty_state()
    state["last_user_message"] = "I want 7 burgers"
    state = graph.invoke(state, {"recursion_limit": 25})
    assert state["status"] == OrderStatus.ORDER_PARTIAL

    state["last_user_message"] = "Yes, I'll take what you have."
    state["messages"] = []
    state = graph.invoke(state, {"recursion_limit": 25})
    assert state["status"] == OrderStatus.ORDER_COMPLETED
    assert state["final_result"]["success"] is True


def test_cook_exhaustion_then_serve_retry():
    graph = build_graph(
        llm=UnavailableLLM(),
        cook_simulator=CookSimulator(["FAIL", "SUCCESS"]),
        serve_simulator=ServeSimulator(["FAIL", "FAIL"]),
    )
    state = empty_state()
    state["last_user_message"] = "I want 1 pizza"
    result = graph.invoke(state, {"recursion_limit": 25})
    assert result["status"] == OrderStatus.ORDER_FAILED
    assert result["cook_attempts_remaining"] == 0
    assert result["serve_attempts_remaining"] == 0
    assert result["cook_attempts_remaining"] >= 0
    assert result["serve_attempts_remaining"] >= 0
