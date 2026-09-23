from __future__ import annotations

from models import OrderItem, OrderStatus
from services.inventory_service import InventoryService


def confirm_order(order_items):
    inventory = InventoryService()
    normalized = []

    for item in order_items:
        if isinstance(item, dict):
            item = OrderItem(
                dish_name=str(item.get("dish_name", "")).strip(),
                requested_quantity=int(item.get("requested_quantity", 0)),
            )
        elif not isinstance(item, OrderItem):
            raise TypeError("Each order item must be an OrderItem or dict.")

        item.available_quantity = inventory.get_available_quantity(item.dish_name)
        if item.available_quantity > 0:
            item.accepted_quantity = min(
                item.requested_quantity, item.available_quantity
            )
        else:
            item.accepted_quantity = 0
        normalized.append(item)

    if not normalized:
        return {"status": OrderStatus.ORDER_NA, "order_items": []}

    if all(item.available_quantity >= item.requested_quantity for item in normalized):
        status = OrderStatus.ORDER_CONFIRMED
    elif all(item.available_quantity == 0 for item in normalized):
        status = OrderStatus.ORDER_NA
    else:
        status = OrderStatus.ORDER_PARTIAL

    return {
        "status": status,
        "order_items": [item.to_dict() for item in normalized],
    }


def order_confirmation_node(state):
    result = confirm_order(state.get("order_items", []))
    state["status"] = result["status"]
    state["order_items"] = [
        OrderItem(
            dish_name=item["dish_name"],
            requested_quantity=item["requested_quantity"],
            available_quantity=item["available_quantity"],
            accepted_quantity=item["accepted_quantity"],
        )
        for item in result["order_items"]
    ]
    return state
