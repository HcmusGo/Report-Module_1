from __future__ import annotations

from exceptions import ValidationError
from models.base import BaseEntity


class MenuItem(BaseEntity):
    """Món trong menu.
    Trường: id, name, price (VNĐ, > 0), prep_minutes (>= 0), tags (set[str]).
    Yêu cầu: thuộc tính private + @property, validate trong setter
    (ném exceptions.ValidationError), to_dict() / from_dict() cho JSON.
    """

    def __init__(self, id: str, name: str, price: int, prep_minutes: int,
                 tags: set[str] | None = None) -> None:
        super().__init__()
        self._id = id
        self.name = name
        self.price = price
        self.prep_minutes = prep_minutes
        self.tags = tags if tags is not None else set()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Tên món không được để trống")
        self._name = value

    @property
    def price(self) -> int:
        return self._price

    @price.setter
    def price(self, value: int) -> None:
        if value <= 0:
            raise ValidationError("Giá tiền (price) phải lớn hơn 0")
        self._price = value

    @property
    def prep_minutes(self) -> int:
        return self._prep_minutes

    @prep_minutes.setter
    def prep_minutes(self, value: int) -> None:
        if value < 0:
            raise ValidationError("Thời gian chuẩn bị (prep_minutes) phải lớn hơn hoặc bằng 0")
        self._prep_minutes = value

    @property
    def tags(self) -> set[str]:
        return self._tags

    @tags.setter
    def tags(self, value: set[str]) -> None:
        if not isinstance(value, set):
            raise ValidationError("Tags phải là một tập hợp (set)")
        self._tags = value

    def to_dict(self) -> dict:
        """Chuyển đổi đối tượng thành dạng dictionary để lưu JSON."""
        return {
            "id": self._id,
            "name": self._name,
            "price": self._price,
            "prep_minutes": self._prep_minutes,
            "tags": list(self._tags)
        }

    @classmethod
    def from_dict(cls, data: dict) -> MenuItem:
        """Tạo đối tượng từ dictionary (dữ liệu JSON)."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            price=data.get("price"),
            prep_minutes=data.get("prep_minutes"),
            tags=set(data.get("tags", []))
        )
