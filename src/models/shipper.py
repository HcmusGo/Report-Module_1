"""Shipper. Người phụ trách: Quyên."""
from __future__ import annotations

from enum import Enum

from models.base import BaseEntity


class ShipperStatus(str, Enum):
    IDLE = "IDLE"        # rảnh, có thể nhận đơn
    BUSY = "BUSY"        # đang giao
    OFFLINE = "OFFLINE"  # nghỉ


class Shipper(BaseEntity):
    """Shipper.

    Trường: id, name, phone, node_id (vị trí hiện tại trên bản đồ), status.
    Phương thức gợi ý: is_idle (property), mark_busy(), mark_idle().
    """

    def __init__(self, id: str, name: str, phone: str, node_id: str,
                 status: ShipperStatus = ShipperStatus.IDLE) -> None:
        raise NotImplementedError("TODO(Quyên)")
