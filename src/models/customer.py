"""Khách hàng. Người phụ trách: Quyên."""
from __future__ import annotations

from models.base import BaseEntity


class Customer(BaseEntity):
    """Khách hàng.

    Trường: id, name, phone, node_id (id của Place nơi khách ở trên bản đồ).
    Validate: tên không rỗng, số điện thoại hợp lệ.
    """

    def __init__(self, id: str, name: str, phone: str, node_id: str) -> None:
        raise NotImplementedError("TODO(Quyên)")
