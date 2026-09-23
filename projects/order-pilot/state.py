from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from models import OrderItem, OrderStatus


class OrderState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    intent: str | None
    order_items: list[OrderItem]
    status: OrderStatus | None
    partial_order_decision: str | None
    error_message: str | None
    final_result: dict[str, Any] | None
    order_attempts_remaining: int
    cook_attempts_remaining: int
    serve_attempts_remaining: int
    last_user_message: str | None
    clarification_required: bool
    pending_action: str | None
    last_operation_id: str | None
    last_cook_result: str | None
    last_serve_result: str | None
