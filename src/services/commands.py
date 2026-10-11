"""Các lệnh cụ thể cho Undo / Redo. Người phụ trách: Tiên (phối hợp Bảo cho lệnh liên quan đường).

Mỗi lệnh giữ đủ thông tin để apply() rồi undo() trả dữ liệu về y như cũ,
kể cả id đơn, trạng thái cũ, shipper cũ, vị trí trong hàng đợi bếp.
"""
from __future__ import annotations

from models.order import Order, OrderStatus
from models.shipper import Shipper
from repositories.base_repository import Repository
from services.history import Command
from services.kitchen_queue import KitchenQueue
from services.road_network import RoadNetwork


class CreateOrderCmd(Command):
    """apply: lưu đơn + đưa vào hàng đợi bếp. undo: xóa đơn + rút khỏi hàng đợi."""

    def __init__(self, orders: Repository[Order], kitchen: KitchenQueue, order: Order) -> None:
        self._orders, self._kitchen, self._order = orders, kitchen, order
        self.description = f"Tạo đơn {order.id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class CancelOrderCmd(Command):
    """apply: đổi trạng thái sang CANCELLED, rút khỏi hàng đợi bếp, trả shipper về IDLE nếu có.
    undo: khôi phục trạng thái cũ, vị trí cũ trong hàng đợi, shipper cũ."""

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 kitchen: KitchenQueue, order_id: str) -> None:
        self._orders, self._shippers, self._kitchen, self._order_id = orders, shippers, kitchen, order_id
        self.description = f"Hủy đơn {order_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class ChangeStatusCmd(Command):
    """Đổi trạng thái hợp lệ (PREPARING, READY, DELIVERED). undo: về trạng thái cũ."""

    def __init__(self, orders: Repository[Order], order_id: str, new_status: OrderStatus) -> None:
        self._orders, self._order_id, self._new_status = orders, order_id, new_status
        self.description = f"Đơn {order_id} → {new_status.value}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class AssignShipperCmd(Command):
    """apply: gán shipper, shipper -> BUSY, đơn -> DELIVERING, ghi delivery_fee.
    undo: trả shipper về IDLE, đơn về READY, xóa shipper_id và delivery_fee."""

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 order_id: str, shipper_id: str, delivery_fee: int) -> None:
        self._orders, self._shippers = orders, shippers
        self._order_id, self._shipper_id, self._fee = order_id, shipper_id, delivery_fee
        self.description = f"Gán shipper {shipper_id} cho đơn {order_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Tiên)")


class SetRoadBlockedCmd(Command):
    """Khóa / mở đường. undo: về giá trị cũ. Nhớ lưu lại map.json qua MapRepository."""

    def __init__(self, network: RoadNetwork, road_id: str, blocked: bool) -> None:
        self._network, self._road_id, self._blocked = network, road_id, blocked
        self.description = ("Khóa" if blocked else "Mở") + f" đường {road_id}"

    def apply(self) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def undo(self) -> None:
        raise NotImplementedError("TODO(Bảo)")
