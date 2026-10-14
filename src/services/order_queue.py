"""Hàng đợi đơn chờ gán shipper (Queue / FIFO). Người phụ trách: Tiên."""
from __future__ import annotations

from collections import deque


class OrderQueue:
    """Đơn vào trước được xử lý trước. Bên trong dùng deque (popleft O(1)).
    Chứa order_id của các đơn WAITING."""

    def __init__(self) -> None:
        self._queue: deque[str] = deque()

    def enqueue(self, order_id: str) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def dequeue(self) -> str | None:
        """Lấy đơn đầu hàng đợi, rỗng thì trả None."""
        raise NotImplementedError("TODO(Tiên)")

    def peek(self) -> str | None:
        raise NotImplementedError("TODO(Tiên)")

    def remove(self, order_id: str) -> bool:
        """Rút một đơn khỏi hàng đợi (khi xóa đơn hoặc gán shipper). O(n)."""
        raise NotImplementedError("TODO(Tiên)")

    def index_of(self, order_id: str) -> int | None:
        """Vị trí của đơn trong hàng đợi (để chụp snapshot trước khi rút ra)."""
        raise NotImplementedError("TODO(Tiên)")

    def insert_at(self, index: int, order_id: str) -> None:
        """Chèn lại đúng vị trí cũ (dùng khi Undo)."""
        raise NotImplementedError("TODO(Tiên)")

    def to_list(self) -> list[str]:
        raise NotImplementedError("TODO(Tiên)")

    def __len__(self) -> int:
        raise NotImplementedError("TODO(Tiên)")
