from __future__ import annotations

from enum import Enum
from exceptions import ValidationError
from models.base import BaseEntity


class OrderStatus(str, Enum):
    WAITING = "WAITING"      # đang chờ trong hàng đợi, chưa có shipper
    ASSIGNED = "ASSIGNED"    # đã gán shipper, nằm trong lộ trình của shipper
    DELIVERED = "DELIVERED"  # đã giao xong


# Luật chuyển trạng thái nằm MỘT chỗ duy nhất này.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.WAITING: {OrderStatus.ASSIGNED},
    OrderStatus.ASSIGNED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


class Order(BaseEntity):
    """Đơn hàng.
    Trường: id, customer_name, pickup_node, delivery_node (id Place), weight_kg (> 0),
    deadline_min (int | None: hạn giao tối đa tính bằng phút kể từ lúc gán), status,
    shipper_id (str | None), note, created_at (ISO string, quyết định thứ tự hàng đợi).
    Validate trong setter (ném exceptions.ValidationError). Có to_dict() / from_dict().
    Chỉ đơn WAITING mới được sửa hoặc xóa (kiểm tra ở OrderService).
    """

    def __init__(self, id: str, customer_name: str, pickup_node: str, delivery_node: str,
                 weight_kg: float, deadline_min: int | None = None,
                 status: OrderStatus = OrderStatus.WAITING, shipper_id: str | None = None,
                 note: str = "", created_at: str = "") -> None:
        super().__init__()
        self._id = id
        self.customer_name = customer_name
        self.pickup_node = pickup_node
        self.delivery_node = delivery_node
        self.weight_kg = weight_kg
        self.deadline_min = deadline_min
        self.status = status
        self.shipper_id = shipper_id
        self.note = note
        self.created_at = created_at

    @property
    def id(self) -> str:
        return self._id

    @property
    def customer_name(self) -> str:
        return self._customer_name

    @customer_name.setter
    def customer_name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Tên khách hàng không được để trống")
        self._customer_name = value

    @property
    def pickup_node(self) -> str:
        return self._pickup_node

    @pickup_node.setter
    def pickup_node(self, value: str) -> None:
        if not value:
            raise ValidationError("Điểm lấy hàng không được để trống")
        self._pickup_node = value

    @property
    def delivery_node(self) -> str:
        return self._delivery_node

    @delivery_node.setter
    def delivery_node(self, value: str) -> None:
        if not value:
            raise ValidationError("Điểm giao hàng không được để trống")
        self._delivery_node = value

    @property
    def weight_kg(self) -> float:
        return self._weight_kg

    @weight_kg.setter
    def weight_kg(self, value: float) -> None:
        if value <= 0:
            raise ValidationError("Trọng lượng weight_kg phải lớn hơn 0")
        self._weight_kg = value

    @property
    def deadline_min(self) -> int | None:
        return self._deadline_min

    @deadline_min.setter
    def deadline_min(self, value: int | None) -> None:
        if value is not None and value <= 0:
            raise ValidationError("Thời hạn deadline_min phải lớn hơn 0")
        self._deadline_min = value

    @property
    def status(self) -> OrderStatus:
        return self._status

    @status.setter
    def status(self, value: OrderStatus) -> None:
        if isinstance(value, str):
            value = OrderStatus(value)
        self._status = value

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "customer_name": self._customer_name,
            "pickup_node": self._pickup_node,
            "delivery_node": self._delivery_node,
            "weight_kg": self._weight_kg,
            "deadline_min": self._deadline_min,
            "status": self._status.value if isinstance(self._status, OrderStatus) else self._status,
            "shipper_id": self.shipper_id,
            "note": self.note,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> Order:
        status_val = data.get("status", OrderStatus.WAITING)
        if isinstance(status_val, str):
            status_val = OrderStatus(status_val)
        return cls(
            id=data.get("id"),
            customer_name=data.get("customer_name"),
            pickup_node=data.get("pickup_node"),
            delivery_node=data.get("delivery_node"),
            weight_kg=data.get("weight_kg"),
            deadline_min=data.get("deadline_min"),
            status=status_val,
            shipper_id=data.get("shipper_id"),
            note=data.get("note", ""),
            created_at=data.get("created_at", "")
        )
