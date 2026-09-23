from __future__ import annotations

import re


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
