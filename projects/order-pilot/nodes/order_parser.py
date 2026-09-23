from __future__ import annotations

import re

from models import OrderItem, OrderStatus
from services.llm_service import LLMService, llm_service
from services.menu_service import MENU, normalize_dish_name

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def parse_quantity(value: str) -> int | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text.isdigit():
        qty = int(text)
        return qty if qty > 0 else None
    return NUMBER_WORDS.get(text)


def parse_order_input(text: str) -> dict:
    if not text or not text.strip():
        return {"intent": "incomplete_order", "order_items": []}

    normalized = text.strip().lower()
    if re.search(
        r"\b(?:capital of france|weather|time|today|who are you|what is)\b", normalized
    ):
        return {"intent": "unrelated", "order_items": []}

    dish_names = sorted(MENU.keys(), key=len, reverse=True)
    item_pattern = "|".join(re.escape(name) for name in dish_names)
    matches = list(
        re.finditer(
            rf"(?P<quantity>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:of\s+)?(?P<dish>{item_pattern})s?\b",
            normalized,
        )
    )

    if matches:
        items = []
        for match in matches:
            quantity = parse_quantity(match.group("quantity"))
            dish = normalize_dish_name(match.group("dish"))
            if quantity is None or quantity <= 0 or not dish:
                return {"intent": "ambiguous", "order_items": []}
            items.append({"dish_name": dish, "requested_quantity": quantity})
        return {"intent": "food_order", "order_items": items}

    if any(dish in normalized for dish in dish_names):
        return {"intent": "incomplete_order", "order_items": []}

    if "food" in normalized or "order" in normalized:
        return {"intent": "incomplete_order", "order_items": []}

    return {"intent": "ambiguous", "order_items": []}


def _to_order_items(raw_items) -> list[OrderItem]:
    items: list[OrderItem] = []
    for item in raw_items or []:
        if isinstance(item, OrderItem):
            items.append(item)
            continue
        dish_name = normalize_dish_name(str(item.get("dish_name", "")))
        quantity = int(item.get("requested_quantity") or item.get("quantity") or 0)
        if not dish_name or quantity <= 0:
            raise ValueError("Invalid order item")
        items.append(
            OrderItem(
                dish_name=dish_name,
                requested_quantity=quantity,
            )
        )
    return items


def semantic_parser_node(state, llm: LLMService | None = None):
    text = state.get("last_user_message") or ""
    service = llm if llm is not None else llm_service
    parsed = None

    if service.available:
        try:
            parsed = service.parse_order_message(text)
        except Exception:
            parsed = None

    if parsed is None:
        parsed = parse_order_input(text)

    intent = parsed.get("intent")
    updates: dict = {
        "intent": intent,
        "clarification_required": intent in {"incomplete_order", "ambiguous"},
        "partial_order_decision": None,
    }

    if intent != "food_order":
        return updates

    try:
        order_items = _to_order_items(parsed.get("order_items", []))
    except Exception:
        return {
            "intent": "incomplete_order",
            "clarification_required": True,
            "partial_order_decision": None,
        }

    if not order_items:
        return {
            "intent": "incomplete_order",
            "clarification_required": True,
            "partial_order_decision": None,
        }

    updates.update(
        {
            "order_items": order_items,
            "status": OrderStatus.ORDER_RECEIVED,
            "pending_action": None,
            "error_message": None,
        }
    )
    return updates
