from __future__ import annotations

from menu_service import get_available_quantity


class InventoryService:
    def get_available_quantity(self, dish_name: str) -> int:
        return get_available_quantity(dish_name)

    def evaluate_order(self, order_items):
        results = []
        for item in order_items:
            available = self.get_available_quantity(item.dish_name)
            accepted = min(item.requested_quantity, available) if available > 0 else 0
            results.append(
                {
                    "dish_name": item.dish_name,
                    "requested_quantity": item.requested_quantity,
                    "available_quantity": available,
                    "accepted_quantity": accepted,
                }
            )
        return results
