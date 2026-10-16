"""CRUD đơn hàng và hàng đợi đơn chờ. Người phụ trách: Tiên."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from exceptions import BusinessRuleError, NotFoundError, ValidationError
from models.map_entities import Place
from models.order import Order, OrderStatus
from repositories.base_repository import Repository
from services.commands import CreateOrderCmd, DeleteOrderCmd, UpdateOrderCmd
from services.history import CommandHistory
from services.order_queue import OrderQueue

# Các trường người dùng được sửa. id, status, shipper_id, created_at do hệ thống quản lý.
EDITABLE_FIELDS = frozenset(
    {"customer_name", "pickup_node", "delivery_node", "weight_kg", "deadline_min", "note"})


class OrderService:
    """Thêm, sửa, xóa, tìm kiếm, lọc đơn. Mọi thay đổi đi qua self._history.execute(Command)
    để Undo / Redo được. Lỗi thì ném exceptions.AppError.

    Luật: chỉ sửa / xóa được đơn WAITING; pickup_node và delivery_node phải là Place có thật
    và khác nhau; kiểm tra giá trị từng trường (khối lượng > 0, hạn giao...) do Order đảm nhận.
    """

    def __init__(self, orders: Repository[Order], places: Repository[Place],
                 queue: OrderQueue, history: CommandHistory,
                 clock: Callable[[], datetime] | None = None) -> None:
        self._orders, self._places = orders, places
        self._queue, self._history = queue, history
        self._clock = clock or datetime.now   # truyền clock giả khi viết test

    # ------------------------------------------------------------------ khởi động
    def restore_queue(self) -> None:
        """Khi khởi động: dựng lại hàng đợi từ các đơn WAITING, sắp theo created_at (hòa thì theo id)."""
        waiting = [o for o in self._orders.get_all() if o.status == OrderStatus.WAITING]
        waiting.sort(key=lambda o: (o.created_at, o.id))
        self._queue.clear()
        for order in waiting:
            self._queue.enqueue(order.id)

    # ------------------------------------------------------------------ thao tác
    def create_order(self, customer_name: str, pickup_node: str, delivery_node: str,
                     weight_kg: float, deadline_min: int | None = None, note: str = "") -> Order:
        self._require_place(pickup_node, "Điểm lấy hàng")
        self._require_place(delivery_node, "Điểm giao hàng")
        if pickup_node == delivery_node:
            raise ValidationError("Điểm lấy hàng và điểm giao hàng phải khác nhau")
        order = Order(
            id=self._orders.next_id(), customer_name=customer_name.strip(),
            pickup_node=pickup_node, delivery_node=delivery_node, weight_kg=weight_kg,
            deadline_min=deadline_min, status=OrderStatus.WAITING, shipper_id=None,
            note=note.strip(), created_at=self._clock().isoformat(timespec="seconds"))
        self._history.execute(CreateOrderCmd(self._orders, self._queue, order))
        return self.get_order(order.id)

    def update_order(self, order_id: str, **changes) -> Order:
        order = self.get_order(order_id)
        self._require_waiting(order, "sửa")
        if not changes:
            raise ValidationError("Không có thông tin nào để sửa")
        unknown = set(changes) - EDITABLE_FIELDS
        if unknown:
            raise ValidationError(f"Không được sửa trường: {', '.join(sorted(unknown))}")
        pickup = changes.get("pickup_node", order.pickup_node)
        delivery = changes.get("delivery_node", order.delivery_node)
        if "pickup_node" in changes:
            self._require_place(pickup, "Điểm lấy hàng")
        if "delivery_node" in changes:
            self._require_place(delivery, "Điểm giao hàng")
        if pickup == delivery:
            raise ValidationError("Điểm lấy hàng và điểm giao hàng phải khác nhau")
        for text_field in ("customer_name", "note"):
            if isinstance(changes.get(text_field), str):
                changes[text_field] = changes[text_field].strip()
        self._history.execute(UpdateOrderCmd(self._orders, order_id, dict(changes)))
        return self.get_order(order_id)

    def delete_order(self, order_id: str) -> None:
        order = self.get_order(order_id)
        self._require_waiting(order, "xóa")
        self._history.execute(DeleteOrderCmd(self._orders, self._queue, order_id))

    # ------------------------------------------------------------------ truy vấn
    def get_order(self, order_id: str) -> Order:
        """Không thấy thì ném NotFoundError."""
        order = self._orders.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}")
        return order

    def list_orders(self, status: OrderStatus | None = None, keyword: str = "") -> list[Order]:
        """Tìm theo từ khóa (mã đơn, tên khách, ghi chú), lọc theo trạng thái; mới nhất trước."""
        kw = keyword.strip().lower()
        result = []
        for order in self._orders.get_all():
            if status is not None and order.status != status:
                continue
            if kw and kw not in f"{order.id} {order.customer_name} {order.note}".lower():
                continue
            result.append(order)
        result.sort(key=lambda o: (o.created_at, o.id), reverse=True)
        return result

    def waiting_orders(self) -> list[Order]:
        """Các đơn đang chờ, đúng thứ tự trong hàng đợi."""
        orders = (self._orders.get_by_id(order_id) for order_id in self._queue.to_list())
        return [o for o in orders if o is not None]

    # ------------------------------------------------------------------ hỗ trợ
    def _require_place(self, node_id: str, label: str) -> None:
        if self._places.get_by_id(node_id) is None:
            raise ValidationError(f"{label} '{node_id}' không có trên bản đồ")

    @staticmethod
    def _require_waiting(order: Order, action: str) -> None:
        if order.status != OrderStatus.WAITING:
            raise BusinessRuleError(
                f"Chỉ {action} được đơn đang chờ, đơn {order.id} đang ở trạng thái {order.status.value}")