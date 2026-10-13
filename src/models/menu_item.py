"""Món ăn. Người phụ trách: Quyên."""
from __future__ import annotations

from models.base import BaseEntity


class MenuItem(BaseEntity):
    """Món trong menu.

    Trường: id, name, price (VNĐ, > 0), prep_minutes (>= 0), tags (set[str]).
    Yêu cầu: thuộc tính private + @property, validate trong setter
    (ném exceptions.ValidationError), to_dict() / from_dict() cho JSON.
    """

    def __init__(self, id: str, name: str, price: int, prep_minutes: int,
                 tags: set[str] | None = None) -> None:
        raise NotImplementedError("TODO(Quyên)")
