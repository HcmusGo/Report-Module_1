"""Hàng đợi đơn chờ gán shipper (Queue / FIFO). Người phụ trách: Tiên."""
from __future__ import annotations

from collections import deque


class OrderQueue:

    def __init__(self) -> None:
        self._queue: deque[str] = deque()

    def enqueue(self, order_id: str) -> None:
        if order_id in self._queue:
            raise ValueError(f"Đơn {order_id} đã có trong hàng đợi")
        self._queue.append(order_id)

    def dequeue(self) -> str | None:
        return self._queue.popleft() if self._queue else None

    def peek(self) -> str | None:
        return self._queue[0] if self._queue else None

    def remove(self, order_id: str) -> bool:
        try:
            self._queue.remove(order_id)
        except ValueError:
            return False
        return True

    def index_of(self, order_id: str) -> int | None:
        try:
            return self._queue.index(order_id)
        except ValueError:
            return None

    def insert_at(self, index: int, order_id: str) -> None:
        if order_id in self._queue:
            raise ValueError(f"Đơn {order_id} đã có trong hàng đợi")
        index = max(0, min(index, len(self._queue)))
        self._queue.insert(index, order_id)

    def clear(self) -> None:
        self._queue.clear()

    def to_list(self) -> list[str]:
        return list(self._queue)

    def __len__(self) -> int:
        return len(self._queue)

    def __contains__(self, order_id: object) -> bool:
        return order_id in self._queue