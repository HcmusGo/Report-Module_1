"""Repository giả lưu trong bộ nhớ, dùng cho test của Service (không đọc ghi file).

Tuân theo đúng giao diện Repository nên Service không biết đây là hàng giả.
Người phụ trách: Tiên.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Generic

from exceptions import NotFoundError, ValidationError
from repositories.base_repository import Repository, T


class InMemoryRepository(Repository[T], Generic[T]):
    def __init__(self, items: Iterable[T] = (), prefix: str = "X") -> None:
        self._items: dict[str, T] = {e.id: e for e in items}
        self._prefix = prefix

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def get_by_id(self, entity_id: str) -> T | None:
        return self._items.get(entity_id)

    def add(self, entity: T) -> None:
        if entity.id in self._items:
            raise ValidationError(f"Trùng id {entity.id}")
        self._items[entity.id] = entity

    def update(self, entity: T) -> None:
        if entity.id not in self._items:
            raise NotFoundError(f"Không có {entity.id}")
        self._items[entity.id] = entity

    def delete(self, entity_id: str) -> T | None:
        return self._items.pop(entity_id, None)

    def next_id(self) -> str:
        numbers = [int(m.group()) for i in self._items if (m := re.search(r"\d+$", i))]
        return f"{self._prefix}{max(numbers, default=0) + 1:03d}"