"""Hàng đợi bếp (Queue / FIFO). Người phụ trách: Tiên."""
from __future__ import annotations

from collections import deque


class KitchenQueue:
    """Đơn vào trước được làm trước. Bên trong dùng deque (popleft O(1))."""

    def __init__(self) -> None:
        self._queue: deque[str] = deque()   # chứa order_id

    def enqueue(self, order_id: str) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def dequeue(self) -> str | None:
        """Lấy đơn đầu hàng đợi, rỗng thì trả None."""
        raise NotImplementedError("TODO(Tiên)")

    def peek(self) -> str | None:
        raise NotImplementedError("TODO(Tiên)")

    def remove(self, order_id: str) -> bool:
        """Rút một đơn khỏi hàng đợi (khi hủy đơn). Trả True nếu có. O(n)."""
        raise NotImplementedError("TODO(Tiên)")

    def to_list(self) -> list[str]:
        """Danh sách order_id theo thứ tự chờ, để UI hiển thị."""
        raise NotImplementedError("TODO(Tiên)")

    def __len__(self) -> int:
        raise NotImplementedError("TODO(Tiên)")
