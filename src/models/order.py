"""Đơn hàng. Người phụ trách: Quyên."""
from __future__ import annotations

from enum import Enum
from typing import Any

from models.base import BaseEntity


class OrderStatus(str, Enum):
    NEW = "NEW"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Sơ đồ trạng thái trong README mục 6. Đây là luật nghiệp vụ DUY NHẤT về chuyển trạng thái.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.NEW: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.DELIVERING, OrderStatus.CANCELLED},
    OrderStatus.DELIVERING: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


class OrderItem:
    """Một dòng món trong đơn (value object, không có id riêng).

    Trường: menu_id, name, unit_price (chụp giá lúc đặt), quantity (>= 1).
    Property: subtotal = unit_price * quantity. Có to_dict() / from_dict().
    """

    def __init__(self, menu_id: str, name: str, unit_price: int, quantity: int) -> None:
        raise NotImplementedError("TODO(Quyên)")

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError("TODO(Quyên)")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrderItem":
        raise NotImplementedError("TODO(Quyên)")


class Order(BaseEntity):
    """Đơn hàng.

    Trường: id, customer_id, items (list[OrderItem]), status (OrderStatus),
    shipper_id (str | None), created_at (ISO string), delivery_fee (int), note.
    Property: subtotal (tổng tiền món), total (= subtotal + delivery_fee).
    Phương thức: change_status(target) -> ném BusinessRuleError nếu
    can_transition() trả False. Có to_dict() / from_dict().
    """

    def __init__(self, id: str, customer_id: str, items: list[OrderItem],
                 status: OrderStatus = OrderStatus.NEW, shipper_id: str | None = None,
                 created_at: str = "", delivery_fee: int = 0, note: str = "") -> None:
        raise NotImplementedError("TODO(Quyên)")
