"""CRUD đơn hàng và hàng đợi đơn chờ. Người phụ trách: Tiên."""
from __future__ import annotations

from models.map_entities import Place
from models.order import Order, OrderStatus
from repositories.base_repository import Repository
from services.history import CommandHistory
from services.order_queue import OrderQueue


class OrderService:
    """Thêm, sửa, xóa, tìm kiếm, lọc đơn. Mọi thay đổi đi qua self._history.execute(Command)
    để Undo / Redo được. Lỗi thì ném exceptions.AppError.

    Luật: chỉ sửa / xóa được đơn WAITING; pickup_node và delivery_node phải là Place có thật;
    weight_kg > 0; deadline_min là None hoặc > 0.
    """

    def __init__(self, orders: Repository[Order], places: Repository[Place],
                 queue: OrderQueue, history: CommandHistory) -> None:
        self._orders, self._places = orders, places
        self._queue, self._history = queue, history

    def restore_queue(self) -> None:
        """Khi khởi động: dựng lại hàng đợi từ các đơn WAITING, sắp theo created_at."""
        raise NotImplementedError("TODO(Tiên)")

    def create_order(self, customer_name: str, pickup_node: str, delivery_node: str,
                     weight_kg: float, deadline_min: int | None = None, note: str = "") -> Order:
        raise NotImplementedError("TODO(Tiên)")

    def update_order(self, order_id: str, **changes) -> Order:
        raise NotImplementedError("TODO(Tiên)")

    def delete_order(self, order_id: str) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def get_order(self, order_id: str) -> Order:
        """Không thấy thì ném NotFoundError."""
        raise NotImplementedError("TODO(Tiên)")

    def list_orders(self, status: OrderStatus | None = None, keyword: str = "") -> list[Order]:
        """Tìm theo từ khóa (tên khách, ghi chú), lọc theo trạng thái; mới nhất trước."""
        raise NotImplementedError("TODO(Tiên)")

    def waiting_orders(self) -> list[Order]:
        """Các đơn đang chờ, đúng thứ tự trong hàng đợi."""
        raise NotImplementedError("TODO(Tiên)")
