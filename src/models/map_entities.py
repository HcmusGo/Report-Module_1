from __future__ import annotations

from enum import Enum

import config
from exceptions import ValidationError
from models.base import BaseEntity


class PlaceKind(str, Enum):
    SHOP = "SHOP"
    JUNCTION = "JUNCTION"
    HOME = "HOME"


class TrafficLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Place(BaseEntity):
    """Nút trên bản đồ, có tọa độ và loại địa điểm."""

    def __init__(
        self,
        id: str,
        name: str,
        x: float,
        y: float,
        kind: PlaceKind = PlaceKind.JUNCTION,
    ) -> None:
        super().__init__()
        self._id = id
        self.name = name
        self.x = x
        self.y = y
        self.kind = kind

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Tên địa điểm không được để trống")
        self._name = value

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValidationError("Tọa độ x phải là một số")
        self._x = float(value)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValidationError("Tọa độ y phải là một số")
        self._y = float(value)

    @property
    def kind(self) -> PlaceKind:
        return self._kind

    @kind.setter
    def kind(self, value: PlaceKind | str) -> None:
        if isinstance(value, str):
            try:
                value = PlaceKind(value)
            except ValueError:
                raise ValidationError("Loại địa điểm không hợp lệ") from None
        if not isinstance(value, PlaceKind):
            raise ValidationError("Loại địa điểm không hợp lệ")
        self._kind = value

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "x": self._x,
            "y": self._y,
            "kind": self._kind.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Place:
        kind_val = data.get("kind", PlaceKind.JUNCTION)
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            kind=kind_val,
        )


class Road(BaseEntity):
    """Cạnh hai chiều nối hai nút trên bản đồ."""

    def __init__(
        self,
        id: str,
        a: str,
        b: str,
        distance_km: float,
        traffic: TrafficLevel = TrafficLevel.MEDIUM,
    ) -> None:
        super().__init__()
        self._id = id
        self.a = a
        self.b = b
        self.distance_km = distance_km
        self.traffic = traffic

    @property
    def id(self) -> str:
        return self._id

    @property
    def a(self) -> str:
        return self._a

    @a.setter
    def a(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Điểm bắt đầu a của đường không được để trống")
        self._a = value

    @property
    def b(self) -> str:
        return self._b

    @b.setter
    def b(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Điểm kết thúc b của đường không được để trống")
        self._b = value

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @distance_km.setter
    def distance_km(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValidationError("Khoảng cách phải là một số")
        if value <= 0:
            raise ValidationError("Khoảng cách distance_km phải lớn hơn 0")
        self._distance_km = float(value)

    @property
    def traffic(self) -> TrafficLevel:
        return self._traffic

    @traffic.setter
    def traffic(self, value: TrafficLevel | str) -> None:
        if isinstance(value, str):
            try:
                value = TrafficLevel(value)
            except ValueError:
                raise ValidationError("Mức giao thông không hợp lệ") from None
        if not isinstance(value, TrafficLevel):
            raise ValidationError("Mức giao thông không hợp lệ")
        self._traffic = value

    @property
    def minutes(self) -> float:
        speed_dict = getattr(config, "TRAFFIC_SPEED_KMH", {
            "LOW": 40.0,
            "MEDIUM": 25.0,
            "HIGH": 10.0,
        })

        speed = speed_dict.get(self._traffic.value) or speed_dict.get(self._traffic, 25.0)

        if speed <= 0:
            speed = 25.0

        return (self._distance_km / speed) * 60.0

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "a": self._a,
            "b": self._b,
            "distance_km": self._distance_km,
            "traffic": self._traffic.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Road:
        traffic_val = data.get("traffic", TrafficLevel.MEDIUM)
        return cls(
            id=data.get("id"),
            a=data.get("a"),
            b=data.get("b"),
            distance_km=data.get("distance_km"),
            traffic=traffic_val,
        )
