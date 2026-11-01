"""
[M2] Owner: Thân Văn Thế Lâm
File: src/models/customer.py

Nhiệm vụ:
- Customer(BaseEntity): thực thể Khách hàng với các thuộc tính id, name, email, is_vip, node_id.
- Đóng gói thuộc tính private (_name, _email, _is_vip, _node_id)
  và cung cấp @property kèm validation.
- Phương thức to_dict() và @classmethod from_dict() chuyển đổi dữ liệu an toàn.
"""

from __future__ import annotations

from typing import Any

from src.models.base import BaseEntity


class Customer(BaseEntity):
    """Thực thể Khách hàng trong hệ thống, kế thừa từ BaseEntity."""

    def __init__(
        self,
        id: str,
        name: str,
        email: str,
        is_vip: bool,
        node_id: str,
    ) -> None:
        """Khởi tạo thực thể Khách hàng với các thuộc tính được kiểm tra hợp lệ."""
        super().__init__(id=id)
        self.name = name
        self.email = email
        self.is_vip = is_vip
        self.node_id = node_id

    @property
    def name(self) -> str:
        """Tên của khách hàng."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Tên khách hàng không được để trống.")
        self._name = value.strip()

    @property
    def email(self) -> str:
        """Email liên hệ của khách hàng."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip() or "@" not in value:
            raise ValueError("Email khách hàng không hợp lệ.")
        self._email = value.strip()

    @property
    def is_vip(self) -> bool:
        """Trạng thái khách hàng VIP."""
        return self._is_vip

    @is_vip.setter
    def is_vip(self, value: bool) -> None:
        self._is_vip = bool(value)

    @property
    def node_id(self) -> str:
        """Mã điểm giao hàng mặc định của khách trên đồ thị."""
        return self._node_id

    @node_id.setter
    def node_id(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Điểm giao hàng không được để trống.")
        self._node_id = value.strip()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển đổi thực thể khách hàng thành dictionary JSON."""
        data = super().to_dict()
        data.update({
            "name": self._name,
            "email": self._email,
            "is_vip": self._is_vip,
            "node_id": self._node_id,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Customer:
        """Khôi phục đối tượng Customer từ dictionary JSON."""
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu đầu vào phải là dictionary.")

        for field in ("id", "name", "email", "node_id"):
            if field not in data or data[field] is None:
                raise ValueError(f"Dữ liệu thiếu trường '{field}'.")

        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            is_vip=bool(data.get("is_vip", False)),
            node_id=str(data["node_id"]),
        )

    def __repr__(self) -> str:
        return (
            f"Customer(id='{self._id}', name='{self._name}', "
            f"email='{self._email}', is_vip={self._is_vip}, node_id='{self._node_id}')"
        )
