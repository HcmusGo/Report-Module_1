"""Shipper và lộ trình của shipper. Người phụ trách: Quyên."""
from __future__ import annotations

from collections import deque
from enum import Enum

from models.base import BaseEntity


class StopKind(str, Enum):
    PICKUP = "PICKUP"      # điểm lấy hàng
    DELIVERY = "DELIVERY"  # điểm giao hàng


class Stop:
    """Một điểm dừng trong lộ trình (value object): order_id, node_id, kind (StopKind).
    Có to_dict() / from_dict()."""

    def __init__(self, order_id: str, node_id: str, kind: StopKind) -> None:
        raise NotImplementedError("TODO(Quyên)")


class Shipper(BaseEntity):
    """Shipper.

    Trường: id, name, node_id (vị trí hiện tại), capacity_kg (sức chở tối đa),
    load_kg (tải trọng hiện tại = tổng khối lượng các đơn đã nhận mà chưa giao),
    route: deque[Stop] (Queue: các điểm lấy / giao đã nhận, chưa hoàn thành, theo thứ tự).
    Property: free_capacity_kg = capacity_kg - load_kg; last_node_id = điểm cuối của route
    (hoặc node_id nếu route rỗng). Có to_dict() / from_dict() (route lưu thành list).
    """

    def __init__(self, id: str, name: str, node_id: str, capacity_kg: float,
                 load_kg: float = 0.0, route: "deque[Stop] | None" = None) -> None:
        raise NotImplementedError("TODO(Quyên)")
