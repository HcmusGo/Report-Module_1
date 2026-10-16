from __future__ import annotations

from enum import Enum
import config
from exceptions import ValidationError
from models.base import BaseEntity


class PlaceKind(str, Enum):
    SHOP = "SHOP"          # cửa hàng, điểm lấy hàng
    JUNCTION = "JUNCTION"  # ngã tư
    HOME = "HOME"          # điểm giao hàng


class TrafficLevel(str, Enum):
    LOW = "LOW"        # vắng
    MEDIUM = "MEDIUM"  # vừa
    HIGH = "HIGH"      # đông


class Place(BaseEntity):
    """Nút trên bản đồ. Trường: id, name, x, y (toạ độ để vẽ), kind (PlaceKind)."""

    def __init__(self, id: str, name: str, x: float, y: float,
                 kind: PlaceKind = PlaceKind.JUNCTION) -> None:
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
            value = PlaceKind(value)
        self._kind = value

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "x": self._x,
            "y": self._y,
            "kind": self._kind.value if isinstance(self._kind, PlaceKind) else self._kind
        }

    @classmethod
    def from_dict(cls, data: dict) -> Place:
        kind_val = data.get("kind", PlaceKind.JUNCTION)
        if isinstance(kind_val, str):
            kind_val = PlaceKind(kind_val)
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            kind=kind_val
        )


class Road(BaseEntity):
    """Cạnh hai chiều nối hai Place.

    Trường: id, a, b (id hai nút), distance_km (> 0), traffic (TrafficLevel).
    Property `minutes` = distance_km / config.TRAFFIC_SPEED_KMH[traffic] * 60, luôn >= 0
    (Dijkstra không chạy với trọng số âm).
    """

    def __init__(self, id: str, a: str, b: str, distance_km: float,
                 traffic: TrafficLevel = TrafficLevel.MEDIUM) -> None:
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
        if not value:
            raise ValidationError("Điểm bắt đầu a của đường không được để trống")
        self._a = value

    @property
    def b(self) -> str:
        return self._b

    @b.setter
    def b(self, value: str) -> None:
        if not value:
            raise ValidationError("Điểm kết thúc b của đường không được để trống")
        self._b = value

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @distance_km.setter
    def distance_km(self, value: float) -> None:
        if value <= 0:
            raise ValidationError("Khoảng cách distance_km phải lớn hơn 0")
        self._distance_km = float(value)

    @property
    def traffic(self) -> TrafficLevel:
        return self._traffic

    @traffic.setter
    def traffic(self, value: TrafficLevel | str) -> None:
        if isinstance(value, str):
            value = TrafficLevel(value)
        self._traffic = value

    @property
    def minutes(self) -> float:
        # Lấy tốc độ ứng với mức độ kẹt xe từ file config.py, mặc định là 30 km/h nếu không tìm thấy
        speed_dict = getattr(config, "TRAFFIC_SPEED_KMH", {
            TrafficLevel.LOW: 40.0,
            TrafficLevel.MEDIUM: 30.0,
            TrafficLevel.HIGH: 15.0
        })
        speed = speed_dict.get(self._traffic, 30.0)
        if speed <= 0:
            speed = 30.0
        return (self._distance_km / speed) * 60.0

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "a": self._a,
            "b": self._b,
            "distance_km": self._distance_km,
            "traffic": self._traffic.value if isinstance(self._traffic, TrafficLevel) else self._traffic
        }

    @classmethod
    def from_dict(cls, data: dict) -> Road:
        traffic_val = data.get("traffic", TrafficLevel.MEDIUM)
        if isinstance(traffic_val, str):
            traffic_val = TrafficLevel(traffic_val)
        return cls(
            id=data.get("id"),
            a=data.get("a"),
            b=data.get("b"),
            distance_km=data.get("distance_km"),
            traffic=traffic_val
        )
