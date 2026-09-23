from __future__ import annotations

import random

from ..models import OrderStatus


class ServeSimulator:
    def __init__(self, outcomes=None):
        self.sequence = list(outcomes or [])
        self.index = 0

    def run(self) -> str:
        if self.sequence:
            outcome = self.sequence[self.index]
            self.index += 1
            return str(outcome).upper()
        return "FAIL" if random.random() < 0.33 else "SUCCESS"


def serve_order(state, simulator: ServeSimulator | None = None):
    sim = simulator or ServeSimulator()
    remaining = int(state.get("serve_attempts_remaining", 2))

    if remaining <= 0:
        state["status"] = OrderStatus.ORDER_FAILED
        state["error_message"] = "Serve attempts exhausted."
        state["final_result"] = {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        }
        return state

    state["serve_attempts_remaining"] = remaining - 1
    state["status"] = OrderStatus.ORDER_SERVING
    outcome = sim.run()

    if outcome == "SUCCESS":
        state["status"] = OrderStatus.ORDER_COMPLETED
        state["final_result"] = {
            "success": True,
            "status": OrderStatus.ORDER_COMPLETED.value,
        }
        state["error_message"] = None
    else:
        state["status"] = OrderStatus.ORDER_FAILED
        state["final_result"] = {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        }
        state["error_message"] = "Serve failed."

    return state


def serve_node(state, simulator: ServeSimulator | None = None):
    return serve_order(state, simulator)
