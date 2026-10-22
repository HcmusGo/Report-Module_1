"""
[M3] Owner: Nguyễn Lê Đức Bảo
File: src/models/menu_item.py

Nhiệm vụ:
- MenuItem(BaseEntity): món ăn (id, tên, giá, thời gian chế biến, ...).
- Đóng gói bằng `_attr`, dùng `@property` có getter/setter kiểm tra hợp lệ.
"""

from __future__ import annotations

from typing import Any

try:
    from models.base import BaseEntity
except ModuleNotFoundError:
    from src.models.base import BaseEntity


class MenuItem(BaseEntity):
    """Lớp biểu diễn món ăn trong thực đơn, kế thừa từ BaseEntity."""

    def __init__(
        self,
        id: str,
        name: str,
        price: float | int,
        prep_time: int | float,
        category: str = "Món chính",
        available: bool = True,
    ) -> None:
        """Khởi tạo thực thể món ăn với kiểm tra hợp lệ thông qua property setters."""
        super().__init__(id=id)
        self.name = name
        self.price = price
        self.prep_time = prep_time
        self.category = category
        self.available = available

    @property
    def name(self) -> str:
        """Tên món ăn (chuỗi không rỗng sau khi strip)."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Tên món ăn phải là chuỗi không rỗng.")
        self._name = value.strip()

    @property
    def price(self) -> float | int:
        """Giá món ăn (số không âm >= 0)."""
        return self._price

    @price.setter
    def price(self, value: float | int) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Giá món ăn phải là số.")
        if value < 0:
            raise ValueError("Giá món ăn không được âm.")
        self._price = value

    @property
    def prep_time(self) -> int | float:
        """Thời gian chế biến tính bằng phút (số > 0)."""
        return self._prep_time

    @prep_time.setter
    def prep_time(self, value: int | float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Thời gian chế biến phải là số.")
        if value <= 0:
            raise ValueError("Thời gian chế biến phải lớn hơn 0 phút.")
        self._prep_time = value

    @property
    def prep_minutes(self) -> int | float:
        """Alias cho prep_time để đảm bảo tương thích khi Module khác gọi."""
        return self.prep_time

    @prep_minutes.setter
    def prep_minutes(self, value: int | float) -> None:
        self.prep_time = value

    @property
    def category(self) -> str:
        """Danh mục món ăn (ví dụ: Món chính, Đồ uống, ...)."""
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Danh mục món ăn phải là chuỗi.")
        self._category = value.strip() or "Món chính"

    @property
    def available(self) -> bool:
        """Trạng thái phục vụ (True: đang phục vụ, False: tạm hết)."""
        return self._available

    @available.setter
    def available(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Trạng thái khả dụng phải là kiểu boolean.")
        self._available = value

    def to_dict(self) -> dict[str, Any]:
        """Chuyển đổi thực thể MenuItem thành dictionary để lưu trữ JSON."""
        return {
            "id": self._id,
            "name": self._name,
            "price": self._price,
            "prep_time": self._prep_time,
            "category": self._category,
            "available": self._available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MenuItem:
        """Khởi tạo MenuItem từ dictionary đọc từ JSON.

        Hỗ trợ đọc cả khóa 'prep_time' lẫn 'prep_minutes'.
        """
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu đầu vào phải là dictionary.")
        if "id" not in data:
            raise ValueError("Dữ liệu thiếu trường 'id'.")
        if "name" not in data:
            raise ValueError("Dữ liệu thiếu trường 'name'.")
        if "price" not in data:
            raise ValueError("Dữ liệu thiếu trường 'price'.")

        prep_val = data.get("prep_time")
        if prep_val is None:
            prep_val = data.get("prep_minutes")
        if prep_val is None:
            raise ValueError("Dữ liệu thiếu trường 'prep_time' hoặc 'prep_minutes'.")

        category = str(data.get("category", "Món chính"))
        available = bool(data.get("available", True))

        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            price=data["price"],
            prep_time=prep_val,
            category=category,
            available=available,
        )

    def __repr__(self) -> str:
        return (
            f"MenuItem(id='{self._id}', name='{self._name}', price={self._price}, "
            f"prep_time={self._prep_time}, category='{self._category}', available={self._available})"
        )
