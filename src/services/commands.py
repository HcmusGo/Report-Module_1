"""Các lệnh cụ thể cho Undo / Redo. Người phụ trách: Tiên.

Mọi lệnh tuân theo QUY TẮC SNAPSHOT trong history.Command: apply() chụp lại phần dữ liệu
sắp đổi vào các thuộc tính `_before_*`, undo() khôi phục đúng từ đó.
"""
from __future__ import annotations

from models.order import Order
from models.shipper import Shipper
from repositories.base_repository import Repository
from services.history import Command
from services.order_queue import OrderQueue


class CreateOrderCmd(Command):
    """apply: lưu đơn + đưa vào hàng đợi. undo: xóa đơn + rút khỏi hàng đợi.
    Snapshot: chính đơn vừa tạo (giữ id) để Redo thêm lại đúng đơn đó."""

    def __init__(self, orders: Repository[Order], queue: OrderQueue, order: Order) -> None:
        self._orders, self._queue, self._order = orders, queue, order
        self.description = f"Tạo đơn {order.id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class UpdateOrderCmd(Command):
    """Sửa đơn WAITING. Snapshot: order.to_dict() TRƯỚC khi sửa (_before_order)."""

    def __init__(self, orders: Repository[Order], order_id: str, changes: dict) -> None:
        self._orders, self._order_id, self._changes = orders, order_id, changes
        self._before_order: dict | None = None
        self.description = f"Sửa đơn {order_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class DeleteOrderCmd(Command):
    """Xóa đơn WAITING. Snapshot: đơn bị xóa (_before_order) và vị trí trong hàng đợi
    (_before_queue_index) để undo đặt lại đúng chỗ, không đẩy xuống cuối hàng."""

    def __init__(self, orders: Repository[Order], queue: OrderQueue, order_id: str) -> None:
        self._orders, self._queue, self._order_id = orders, queue, order_id
        self._before_order: dict | None = None
        self._before_queue_index: int | None = None
        self.description = f"Xóa đơn {order_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class AssignOrderCmd(Command):
    """Gán đơn cho shipper: đơn -> ASSIGNED, ghi shipper_id, shipper.load_kg += weight,
    thêm 2 Stop (PICKUP, DELIVERY) vào cuối route, rút đơn khỏi hàng đợi.

    Snapshot trong apply(): _before_order (dict), _before_shipper (dict, gồm cả route và
    load_kg), _before_queue_index. undo() khôi phục từ đó, KHÔNG tự suy ra giá trị."""

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 queue: OrderQueue, order_id: str, shipper_id: str) -> None:
        self._orders, self._shippers, self._queue = orders, shippers, queue
        self._order_id, self._shipper_id = order_id, shipper_id
        self._before_order: dict | None = None
        self._before_shipper: dict | None = None
        self._before_queue_index: int | None = None
        self.description = f"Gán đơn {order_id} cho {shipper_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class CompleteStopCmd(Command):
    """Shipper hoàn thành điểm dừng đầu route (popleft). Nếu là DELIVERY: đơn -> DELIVERED,
    load_kg -= weight. Shipper di chuyển tới node của điểm dừng.

    Snapshot: _before_shipper (dict, gồm route, node_id, load_kg) và _before_order (dict | None)."""

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 shipper_id: str) -> None:
        self._orders, self._shippers, self._shipper_id = orders, shippers, shipper_id
        self._before_shipper: dict | None = None
        self._before_order: dict | None = None
        self.description = f"Hoàn thành điểm dừng của {shipper_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")
