import pytest

from models import OrderItem, OrderStatus
from nodes.order_parser import parse_order_input
from nodes.order_confirmation import confirm_order
from nodes.user_decision import decide_partial_order
from services.menu_service import get_available_quantity
from nodes.cook import CookSimulator
from nodes.serve import ServeSimulator


@pytest.mark.parametrize(
    "text, expected",
    [
        ("I want 2 burgers and 1 pizza", [("burger", 2), ("pizza", 1)]),
        ("Can I get 3 biryani?", [("biryani", 3)]),
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
