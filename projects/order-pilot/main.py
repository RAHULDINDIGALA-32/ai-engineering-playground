from __future__ import annotations

from graph.graph import build_graph
from models import OrderStatus


def main() -> None:
    graph = build_graph()
    state = {
        "messages": [],
        "order_items": [],
        "status": None,
        "partial_order_decision": None,
        "error_message": None,
        "final_result": None,
        "order_attempts_remaining": 3,
        "cook_attempts_remaining": 2,
        "serve_attempts_remaining": 2,
        "last_user_message": None,
    }

    print("Order-Pilot ready. Type your order or 'quit' to exit.")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        state["last_user_message"] = user_input
        result = graph.invoke(state)
        state = result

        final_status = state.get("status")
        final_result = state.get("final_result")
        if final_status in {OrderStatus.ORDER_COMPLETED, OrderStatus.ORDER_FAILED, OrderStatus.ORDER_CANCELLED}:
            if final_result:
                print(f"Final result: {final_result}")
            else:
                print(f"Status: {final_status.value if hasattr(final_status, 'value') else final_status}")
            print("Order session closed.")
            break

        if state.get("status") == OrderStatus.ORDER_PARTIAL:
            print("Assistant: We currently have a partial order available. Would you like to proceed with the available items or place a different order?")
        elif state.get("status") == OrderStatus.ORDER_NA:
            print("Assistant: That order is unavailable. Please submit a new order.")
        elif state.get("status") == OrderStatus.ORDER_CONFIRMED:
            print("Assistant: Your order has been confirmed.")
        else:
            print("Assistant: I'm Order-Pilot, a restaurant ordering assistant. I can help you place food orders, but I can't assist with general questions.")


if __name__ == "__main__":
    main()
