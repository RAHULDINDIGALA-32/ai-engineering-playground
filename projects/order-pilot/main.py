from __future__ import annotations

from langchain_core.messages import HumanMessage

from graph.graph import build_graph, empty_state
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
    state = empty_state()
    state["session_id"] = "sess-cli"

    print("Order-Pilot ready. Type your order or 'quit' to exit.")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        invoke_input = {
            **state,
            "last_user_message": user_input,
            "messages": [HumanMessage(content=user_input)],
        }
        state = graph.invoke(invoke_input, {"recursion_limit": 25})

        _print_last_assistant_message(state)

        final_status = state.get("status")
        if final_status in {
            OrderStatus.ORDER_COMPLETED,
            OrderStatus.ORDER_FAILED,
            OrderStatus.ORDER_CANCELLED,
        }:
            final_result = state.get("final_result")
            if final_result:
                print(f"Final result: {final_result}")
            print("Order session closed.")
            break


if __name__ == "__main__":
    main()
