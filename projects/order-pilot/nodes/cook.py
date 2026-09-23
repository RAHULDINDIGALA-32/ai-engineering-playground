from __future__ import annotations

import random

from ..models import OrderStatus


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
    sim = simulator or CookSimulator()
    remaining = int(state.get("cook_attempts_remaining", 2))

    if remaining <= 0:
        state["status"] = OrderStatus.ORDER_FAILED
        state["error_message"] = "Cook attempts exhausted."
        state["final_result"] = {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        }
        return state

    state["cook_attempts_remaining"] = remaining - 1
    state["status"] = OrderStatus.ORDER_COOKING
    outcome = sim.run()

    if outcome == "SUCCESS":
        state["status"] = OrderStatus.ORDER_READY
        state["error_message"] = None
    else:
        state["status"] = OrderStatus.ORDER_FAILED
        state["error_message"] = "Cook failed."
        state["final_result"] = {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        }

    return state


def cook_node(state, simulator: CookSimulator | None = None):
    return cook_order(state, simulator)
