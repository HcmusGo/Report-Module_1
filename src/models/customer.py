from __future__ import annotations

from exceptions import ValidationError
from models.base import BaseEntity


class Customer(BaseEntity):
    """Khách hàng.
    Trường: id, name, phone, node_id (id của Place nơi khách ở trên bản đồ).
    Validate: tên không rỗng, số điện thoại hợp lệ.
    """

    def __init__(self, id: str, name: str, phone: str, node_id: str) -> None:
        super().__init__()
        self._id = id
        self.name = name
        self.phone = phone
        self.node_id = node_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Tên khách hàng không được để trống")
        self._name = value

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Số điện thoại không được để trống")
        # Kiểm tra cơ bản: số điện thoại phải chứa chữ số và có độ dài hợp lệ (ví dụ từ 9-11 số)
        cleaned_phone = "".join(filter(str.isdigit, value))
        if len(cleaned_phone) < 9 or len(cleaned_phone) > 11:
            raise ValidationError("Số điện thoại không hợp lệ (phải từ 9 đến 11 chữ số)")
        self._phone = value

    @property
    def node_id(self) -> str:
        return self._node_id

    @node_id.setter
    def node_id(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Mã địa điểm node_id của khách hàng không được để trống")
        self._node_id = value

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "phone": self._phone,
            "node_id": self._node_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> Customer:
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            phone=data.get("phone"),
            node_id=data.get("node_id")
        )
