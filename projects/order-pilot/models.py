from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrderStatus(str, Enum):
    ORDER_RECEIVED = "ORDER_RECEIVED"
    ORDER_CONFIRMED = "ORDER_CONFIRMED"
    ORDER_PARTIAL = "ORDER_PARTIAL"
    ORDER_NA = "ORDER_NA"
    ORDER_COOKING = "ORDER_COOKING"
    ORDER_READY = "ORDER_READY"
    ORDER_SERVING = "ORDER_SERVING"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    ORDER_FAILED = "ORDER_FAILED"
    ORDER_CANCELLED = "ORDER_CANCELLED"


@dataclass
class OrderItem:
    dish_name: str
    requested_quantity: int
    available_quantity: int = 0
    accepted_quantity: int = 0

    def to_dict(self) -> dict:
        return {
            "dish_name": self.dish_name,
            "requested_quantity": self.requested_quantity,
            "available_quantity": self.available_quantity,
            "accepted_quantity": self.accepted_quantity,
        }
