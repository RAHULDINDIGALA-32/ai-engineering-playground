from __future__ import annotations

import re

from services.llm_service import LLMService


def decide_partial_order(text: str) -> str:
    if not text:
        return "AMBIGUOUS"

    normalized = text.strip().lower()
    if re.search(
        r"\b(yes|accept|okay|sure|i'll take it|take what you have|proceed)\b",
        normalized,
    ):
        return "ACCEPT_PARTIAL"
    if re.search(
        r"\b(no|reject|new order|different order|something else|not now)\b", normalized
    ):
        return "NEW_ORDER"
    return "AMBIGUOUS"


def partial_decision_node(state):
    text = state.get("last_user_message") or ""
    llm = LLMService()
    if llm.available:
        try:
            state["partial_order_decision"] = llm.parse_partial_decision(text)
            return state
        except Exception:
            pass
    state["partial_order_decision"] = decide_partial_order(text)
    return state
