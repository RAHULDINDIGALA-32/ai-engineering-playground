from __future__ import annotations

import random

from models import OrderStatus


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
    remaining = int(state.get("serve_attempts_remaining", 2))
    if remaining <= 0:
        return {
            "status": OrderStatus.ORDER_FAILED,
            "error_message": "Serve attempts exhausted.",
            "last_serve_result": "FAIL",
            "final_result": {
                "success": False,
                "status": OrderStatus.ORDER_FAILED.value,
            },
        }

    sim = simulator or ServeSimulator()
    new_remaining = remaining - 1
    operation_id = f"{state.get('session_id', 'sess')}-SERVE-{remaining:02d}"
    outcome = sim.run()
    if outcome == "SUCCESS":
        return {
            "serve_attempts_remaining": new_remaining,
            "status": OrderStatus.ORDER_COMPLETED,
            "error_message": None,
            "last_serve_result": "SUCCESS",
            "last_operation_id": operation_id,
            "final_result": {
                "success": True,
                "status": OrderStatus.ORDER_COMPLETED.value,
            },
        }

    if new_remaining > 0:
        return {
            "serve_attempts_remaining": new_remaining,
            "status": OrderStatus.ORDER_SERVING,
            "error_message": "Serve failed.",
            "last_serve_result": "FAIL",
            "last_operation_id": operation_id,
        }

    return {
        "serve_attempts_remaining": new_remaining,
        "status": OrderStatus.ORDER_FAILED,
        "error_message": "Serve failed.",
        "last_serve_result": "FAIL",
        "last_operation_id": operation_id,
        "final_result": {
            "success": False,
            "status": OrderStatus.ORDER_FAILED.value,
        },
    }


def serve_node(state, simulator: ServeSimulator | None = None):
    return serve_order(state, simulator)
