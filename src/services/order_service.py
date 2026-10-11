"""Nghiệp vụ đơn hàng và hàng đợi bếp. Người phụ trách: Tiên."""
from __future__ import annotations

from models.customer import Customer
from models.menu_item import MenuItem
from models.order import Order, OrderStatus
from repositories.base_repository import Repository
from services.history import CommandHistory
from services.kitchen_queue import KitchenQueue


class OrderService:
    """Mọi thay đổi dữ liệu đi qua self._history.execute(Command) để Undo / Redo được.

    Vòng đời: NEW (nằm trong hàng đợi bếp) -> PREPARING -> READY -> (DispatchService lo
    DELIVERING, DELIVERED). Chuyển trạng thái phải qua models.order.can_transition().
    """

    def __init__(self, orders: Repository[Order], menu: Repository[MenuItem],
                 customers: Repository[Customer], kitchen: KitchenQueue,
                 history: CommandHistory) -> None:
        self._orders, self._menu, self._customers = orders, menu, customers
        self._kitchen, self._history = kitchen, history

    def restore_kitchen_queue(self) -> None:
        """Khi khởi động: dựng lại hàng đợi bếp từ các đơn NEW, theo thứ tự created_at."""
        raise NotImplementedError("TODO(Tiên)")

    def create_order(self, customer_id: str, items: dict[str, int], note: str = "") -> Order:
        """items = {menu_id: số lượng}. Kiểm tra khách và món tồn tại, số lượng >= 1."""
        raise NotImplementedError("TODO(Tiên)")

    def cancel_order(self, order_id: str) -> Order:
        """Chỉ hủy được khi NEW, PREPARING hoặc READY."""
        raise NotImplementedError("TODO(Tiên)")

    def start_next_in_kitchen(self) -> Order | None:
        """Lấy đơn đầu hàng đợi: NEW -> PREPARING. Hàng đợi rỗng thì trả None."""
        raise NotImplementedError("TODO(Tiên)")

    def mark_ready(self, order_id: str) -> Order:
        """PREPARING -> READY."""
        raise NotImplementedError("TODO(Tiên)")

    def get_order(self, order_id: str) -> Order:
        """Không thấy thì ném NotFoundError."""
        raise NotImplementedError("TODO(Tiên)")

    def list_orders(self, status: OrderStatus | None = None, customer_id: str | None = None,
                    keyword: str = "") -> list[Order]:
        """Tìm kiếm và lọc, mới nhất trước."""
        raise NotImplementedError("TODO(Tiên)")

    def kitchen_queue(self) -> list[Order]:
        """Các đơn đang chờ bếp, theo thứ tự hàng đợi."""
        raise NotImplementedError("TODO(Tiên)")
