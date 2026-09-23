from __future__ import annotations

import random

from models import OrderStatus


class CookSimulator:
    def __init__(self, outcomes=None):
        self.sequence = list(outcomes or [])
        self.index = 0

    def run(self) -> str:
        if self.sequence:
            outcome = self.sequence[self.index]
            self.index += 1
            return str(outcome).upper()
        return "FAIL" if random.random() < 0.33 else "SUCCESS"


def cook_order(state, simulator: CookSimulator | None = None):
    remaining = int(state.get("cook_attempts_remaining", 2))
    if remaining <= 0:
        return {
            "status": OrderStatus.ORDER_FAILED,
            "error_message": "Cook attempts exhausted.",
            "last_cook_result": "FAIL",
            "final_result": {
                "success": False,
                "status": OrderStatus.ORDER_FAILED.value,
            },
        }

    sim = simulator or CookSimulator()
    new_remaining = remaining - 1
    operation_id = f"{state.get('session_id', 'sess')}-COOK-{remaining:02d}"
    outcome = sim.run()
    if outcome == "SUCCESS":
        return {
            "cook_attempts_remaining": new_remaining,
            "status": OrderStatus.ORDER_READY,
            "error_message": None,
            "last_cook_result": "SUCCESS",
            "last_operation_id": operation_id,
        }

    if new_remaining > 0:
        return {
            "cook_attempts_remaining": new_remaining,
            "status": OrderStatus.ORDER_COOKING,
            "error_message": "Cook failed.",
            "last_cook_result": "FAIL",
            "last_operation_id": operation_id,
        }

    return {
        "cook_attempts_remaining": new_remaining,
        "status": OrderStatus.ORDER_FAILED,
        "error_message": "Cook failed.",
        "last_cook_result": "FAIL",
        "last_operation_id": operation_id,
        "final_result": {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        },
    }


def cook_node(state, simulator: CookSimulator | None = None):
    return cook_order(state, simulator)
