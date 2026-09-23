from __future__ import annotations


def generate_response(state, kind: str = "default") -> str:
    if kind == "unrelated":
        return "I'm Order-Pilot, a restaurant ordering assistant. I can help you place food orders, but I can't assist with general questions."
    if kind == "partial":
        return "We currently have a partial order available. Would you like to proceed with the available items or place a different order?"
    if kind == "clarify":
        return "Please provide the quantity for the item you want."
    if kind == "success":
        return "Your order has been prepared and served successfully. Thank you!"
    if kind == "failure":
        return "I'm sorry, but we weren't able to complete your order after the available attempts. Please try again later."
    return "Please enter a valid food order."
