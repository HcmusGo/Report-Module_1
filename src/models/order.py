"""Đơn hàng. Người phụ trách: Quyên."""
from __future__ import annotations

from enum import Enum

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
        raise NotImplementedError("TODO(Quyên)")
