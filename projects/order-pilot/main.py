from __future__ import annotations

from graph.graph import build_graph
from models import OrderStatus


def _print_last_assistant_message(state):
    messages = state.get("messages", [])
    if not messages:
        return
    last_message = messages[-1]
    if isinstance(last_message, dict):
        content = last_message.get("content")
    else:
        content = getattr(last_message, "content", str(last_message))
    if content:
        print(f"Assistant: {content}")


def main() -> None:
    graph = build_graph()
    state = {
        "messages": [],
        "intent": None,
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
        state = graph.invoke(state)

        final_status = state.get("status")
        final_result = state.get("final_result")
        if final_status in {
            OrderStatus.ORDER_COMPLETED,
            OrderStatus.ORDER_FAILED,
            OrderStatus.ORDER_CANCELLED,
        }:
            _print_last_assistant_message(state)
            if final_result:
                print(f"Final result: {final_result}")
            else:
                print(
                    f"Status: {final_status.value if hasattr(final_status, 'value') else final_status}"
                )
            print("Order session closed.")
            break

        _print_last_assistant_message(state)


if __name__ == "__main__":
    main()
