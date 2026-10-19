"""Các lệnh cụ thể cho Undo / Redo. Người phụ trách: Tiên.

Mọi lệnh tuân theo QUY TẮC SNAPSHOT trong history.Command: apply() chụp lại phần dữ liệu
sắp đổi vào các thuộc tính `_before_*`, undo() khôi phục đúng từ đó, không gán cứng giá trị.

Cách làm chung để không phụ thuộc vào setter của models:
- Snapshot = copy.deepcopy(entity.to_dict()), một bản sao độc lập.
- Sửa dữ liệu = lấy dict, đổi giá trị, dựng lại entity bằng from_dict() (nên việc kiểm tra
  hợp lệ của model chạy TRƯỚC khi ghi, lỗi thì chưa có gì bị thay đổi) rồi repo.update().
- Khôi phục = dựng lại entity từ snapshot rồi repo.update() (hoặc repo.add() nếu đã bị xóa).
"""
from __future__ import annotations

import copy

from exceptions import BusinessRuleError, NotFoundError
from models.order import Order, OrderStatus, can_transition
from models.shipper import Shipper, StopKind
from repositories.base_repository import Repository, T
from services.history import Command
from services.order_queue import OrderQueue


def _snapshot(entity) -> dict:
    """Bản sao độc lập của entity dưới dạng dict."""
    return copy.deepcopy(entity.to_dict())


def _require(repo: Repository[T], entity_id: str, label: str) -> T:
    entity = repo.get_by_id(entity_id)
    if entity is None:
        raise NotFoundError(f"Không tìm thấy {label} {entity_id}")
    return entity


def _enum_value(value) -> str:
    """Giá trị chuỗi của một Enum, hoặc chính chuỗi đó nếu đã là chuỗi."""
    return str(getattr(value, "value", value))


class CreateOrderCmd(Command):


    def __init__(self, orders: Repository[Order], queue: OrderQueue, order: Order) -> None:
        self._orders, self._queue, self._order = orders, queue, order
        self._snapshot: dict | None = None
        self.description = f"Tạo đơn {order.id}"

    def apply(self) -> None:
        if self._snapshot is None:
            self._snapshot = _snapshot(self._order)       # chụp đơn vừa tạo, lần đầu
        order = Order.from_dict(copy.deepcopy(self._snapshot))
        self._orders.add(order)
        self._queue.enqueue(self._snapshot["id"])

    def undo(self) -> None:
        self._queue.remove(self._snapshot["id"])
        self._orders.delete(self._snapshot["id"])


class UpdateOrderCmd(Command):


    def __init__(self, orders: Repository[Order], order_id: str, changes: dict) -> None:
        self._orders, self._order_id, self._changes = orders, order_id, changes
        self._before_order: dict | None = None
        self.description = f"Sửa đơn {order_id}"

    def apply(self) -> None:
        order = _require(self._orders, self._order_id, "đơn")
        before = _snapshot(order)                          # chụp trước khi sửa
        data = copy.deepcopy(before)
        data.update(self._changes)
        updated = Order.from_dict(data)                    # kiểm tra hợp lệ trước khi ghi
        self._before_order = before
        self._orders.update(updated)

    def undo(self) -> None:
        self._orders.update(Order.from_dict(copy.deepcopy(self._before_order)))


class DeleteOrderCmd(Command):


    def __init__(self, orders: Repository[Order], queue: OrderQueue, order_id: str) -> None:
        self._orders, self._queue, self._order_id = orders, queue, order_id
        self._before_order: dict | None = None
        self._before_queue_index: int | None = None
        self.description = f"Xóa đơn {order_id}"

    def apply(self) -> None:
        order = _require(self._orders, self._order_id, "đơn")
        self._before_order = _snapshot(order)                       # chụp đơn
        self._before_queue_index = self._queue.index_of(self._order_id)   # chụp vị trí hàng đợi
        self._queue.remove(self._order_id)
        self._orders.delete(self._order_id)

    def undo(self) -> None:
        self._orders.add(Order.from_dict(copy.deepcopy(self._before_order)))
        if self._before_queue_index is not None:
            self._queue.insert_at(self._before_queue_index, self._order_id)


class AssignOrderCmd(Command):

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 queue: OrderQueue, order_id: str, shipper_id: str) -> None:
        self._orders, self._shippers, self._queue = orders, shippers, queue
        self._order_id, self._shipper_id = order_id, shipper_id
        self._before_order: dict | None = None
        self._before_shipper: dict | None = None
        self._before_queue_index: int | None = None
        self.description = f"Gán đơn {order_id} cho {shipper_id}"

    def apply(self) -> None:
        order = _require(self._orders, self._order_id, "đơn")
        shipper = _require(self._shippers, self._shipper_id, "shipper")
        before_order, before_shipper = _snapshot(order), _snapshot(shipper)   # chụp trước khi đổi

        if not can_transition(OrderStatus(_enum_value(before_order["status"])), OrderStatus.ASSIGNED):
            raise BusinessRuleError(f"Đơn {self._order_id} không ở trạng thái chờ nên không gán được")
        new_load = round(before_shipper["load_kg"] + before_order["weight_kg"], 3)
        if new_load > before_shipper["capacity_kg"]:
            raise BusinessRuleError(
                f"Shipper {self._shipper_id} vượt tải: {new_load} kg > {before_shipper['capacity_kg']} kg")

        new_order = copy.deepcopy(before_order)
        new_order["status"] = OrderStatus.ASSIGNED.value
        new_order["shipper_id"] = self._shipper_id
        new_shipper = copy.deepcopy(before_shipper)
        new_shipper["load_kg"] = new_load
        new_shipper["route"] = list(new_shipper["route"]) + [
            {"order_id": self._order_id, "node_id": before_order["pickup_node"],
             "kind": StopKind.PICKUP.value},
            {"order_id": self._order_id, "node_id": before_order["delivery_node"],
             "kind": StopKind.DELIVERY.value},
        ]
        order_obj, shipper_obj = Order.from_dict(new_order), Shipper.from_dict(new_shipper)  # kiểm tra trước khi ghi

        self._before_order, self._before_shipper = before_order, before_shipper
        self._before_queue_index = self._queue.index_of(self._order_id)
        self._orders.update(order_obj)
        self._shippers.update(shipper_obj)
        self._queue.remove(self._order_id)

    def undo(self) -> None:
        self._orders.update(Order.from_dict(copy.deepcopy(self._before_order)))
        self._shippers.update(Shipper.from_dict(copy.deepcopy(self._before_shipper)))
        if self._before_queue_index is not None:
            self._queue.insert_at(self._before_queue_index, self._order_id)


class CompleteStopCmd(Command):

    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 shipper_id: str) -> None:
        self._orders, self._shippers, self._shipper_id = orders, shippers, shipper_id
        self._before_shipper: dict | None = None
        self._before_order: dict | None = None
        self.description = f"Hoàn thành điểm dừng của {shipper_id}"

    def apply(self) -> None:
        shipper = _require(self._shippers, self._shipper_id, "shipper")
        before_shipper = _snapshot(shipper)                        # chụp trước khi đổi
        if not before_shipper["route"]:
            raise BusinessRuleError(f"Shipper {self._shipper_id} không còn điểm dừng nào")

        new_shipper = copy.deepcopy(before_shipper)
        stop = new_shipper["route"].pop(0)                         # lấy điểm dừng đầu hàng
        new_shipper["node_id"] = stop["node_id"]

        before_order: dict | None = None
        new_order_obj: Order | None = None
        if _enum_value(stop["kind"]) == StopKind.DELIVERY.value:
            order = _require(self._orders, stop["order_id"], "đơn")
            before_order = _snapshot(order)
            if not can_transition(OrderStatus(_enum_value(before_order["status"])), OrderStatus.DELIVERED):
                raise BusinessRuleError(f"Đơn {stop['order_id']} không ở trạng thái đã gán nên không giao được")
            new_order = copy.deepcopy(before_order)
            new_order["status"] = OrderStatus.DELIVERED.value
            new_shipper["load_kg"] = round(max(0.0, before_shipper["load_kg"] - before_order["weight_kg"]), 3)
            new_order_obj = Order.from_dict(new_order)
        shipper_obj = Shipper.from_dict(new_shipper)               # kiểm tra trước khi ghi

        self._before_shipper, self._before_order = before_shipper, before_order
        self.description = f"Hoàn thành điểm dừng {_enum_value(stop['kind'])} đơn {stop['order_id']} của {self._shipper_id}"
        if new_order_obj is not None:
            self._orders.update(new_order_obj)
        self._shippers.update(shipper_obj)

    def undo(self) -> None:
        self._shippers.update(Shipper.from_dict(copy.deepcopy(self._before_shipper)))
        if self._before_order is not None:
            self._orders.update(Order.from_dict(copy.deepcopy(self._before_order)))