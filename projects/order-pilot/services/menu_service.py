from __future__ import annotations

MENU = {
    "burger": 5,
    "pizza": 5,
    "biryani": 10,
    "fries": 8,
    "pasta": 6,
    "salad": 4,
    "coke": 50,
}


def normalize_dish_name(dish_name: str) -> str:
    cleaned = (dish_name or "").strip().lower().replace("-", " ")
    collapsed = " ".join(cleaned.split())
    if collapsed.endswith("s") and not collapsed.endswith("ss") and len(collapsed) > 2:
        collapsed = collapsed[:-1]
    return collapsed


def get_available_quantity(dish_name: str) -> int:
    normalized = normalize_dish_name(dish_name)
    if not normalized:
        return 0
    return MENU.get(normalized, 0)


def get_menu_snapshot() -> dict[str, int]:
    return dict(MENU)
