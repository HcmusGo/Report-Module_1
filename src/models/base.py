"""
[CHUNG] Owner: Cả nhóm (đề xuất: Nguyễn Lê Đức Bảo viết trước)
File: src/models/base.py

Nhiệm vụ:
- BaseEntity: lớp cha của mọi entity (GraphNode, MenuItem, Order, ...).
- Thuộc tính private `_id`, `@property id`.
- Phương thức `to_dict()` và `from_dict()` để ghi/đọc JSON.
- Cần chốt sớm vì mọi model đều kế thừa file này.
"""
# [M3] Owner: Nguyễn Lê Đức Bảo

from __future__ import annotations

from typing import Any


class BaseEntity:
    """Lớp thực thể cơ sở (BaseEntity) cho mọi thực thể trong hệ thống."""

    def __init__(self, id: str) -> None:
        if not isinstance(id, str) or not id.strip():
            raise ValueError("ID phải là chuỗi không rỗng.")
        self._id: str = id.strip()

    @property
    def id(self) -> str:
        """Lấy giá trị ID của thực thể."""
        return self._id

    @id.setter
    def id(self, new_id: str) -> None:
        """Cập nhật ID cho thực thể (kiểm tra hợp lệ)."""
        if not isinstance(new_id, str) or not new_id.strip():
            raise ValueError("ID phải là chuỗi không rỗng.")
        self._id = new_id.strip()

    def to_dict(self) -> dict[str, Any]:
        """Chuyển đổi thực thể thành dictionary để lưu trữ JSON."""
        return {"id": self._id}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseEntity:
        """Khởi tạo thực thể từ dictionary đọc từ JSON."""
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu đầu vào phải là dictionary.")
        if "id" not in data:
            raise ValueError("Dữ liệu thiếu trường 'id'.")
        return cls(id=str(data["id"]))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self._id}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        if type(self) is not type(other):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash((self.__class__, self._id))
