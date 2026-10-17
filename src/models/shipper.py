from __future__ import annotations

from collections import deque
from enum import Enum

from exceptions import ValidationError
from models.base import BaseEntity


class StopKind(str, Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"


class Stop:
    def __init__(self, order_id: str, node_id: str, kind: StopKind | str) -> None:
        self.order_id = order_id
        self.node_id = node_id
        self.kind = kind

    @property
    def order_id(self) -> str:
        return self._order_id

    @order_id.setter
    def order_id(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Mã đơn hàng order_id không được để trống")
        self._order_id = value

    @property
    def node_id(self) -> str:
        return self._node_id

    @node_id.setter
    def node_id(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Mã node_id không được để trống")
        self._node_id = value

    @property
    def kind(self) -> StopKind:
        return self._kind

    @kind.setter
    def kind(self, value: StopKind | str) -> None:
        if isinstance(value, str):
            value = StopKind(value)
        self._kind = value

    def to_dict(self) -> dict:
        return {
            "order_id": self._order_id,
            "node_id": self._node_id,
            "kind": self._kind.value if isinstance(self._kind, StopKind) else self._kind
        }

    @classmethod
    def from_dict(cls, data: dict) -> Stop:
        kind_val = data.get("kind", StopKind.PICKUP)
        if isinstance(kind_val, str):
            kind_val = StopKind(kind_val)
        return cls(
            order_id=data.get("order_id"),
            node_id=data.get("node_id"),
            kind=kind_val
        )


class Shipper(BaseEntity):
    def __init__(self, id: str, name: str, node_id: str, capacity_kg: float,
                 load_kg: float = 0.0, route: deque[Stop] | list[Stop] | None = None) -> None:
        super().__init__()
        self._id = id
        self.name = name
        self.node_id = node_id
        self.capacity_kg = capacity_kg
        self.load_kg = load_kg
        self.route = route if route is not None else deque()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Tên shipper không được để trống")
        self._name = value

    @property
    def node_id(self) -> str:
        return self._node_id

    @node_id.setter
    def node_id(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("Vị trí node_id của shipper không được để trống")
        self._node_id = value

    @property
    def capacity_kg(self) -> float:
        return self._capacity_kg

    @capacity_kg.setter
    def capacity_kg(self, value: float) -> None:
        if value <= 0:
            raise ValidationError("Sức chở tối đa capacity_kg phải lớn hơn 0")
        self._capacity_kg = value

    @property
    def load_kg(self) -> float:
        return self._load_kg

    @load_kg.setter
    def load_kg(self, value: float) -> None:
        if value < 0:
            raise ValidationError("Tải trọng hiện tại load_kg không được âm")
        if hasattr(self, "_capacity_kg") and value > self._capacity_kg:
            raise ValidationError("Tải trọng hiện tại load_kg phải từ 0 đến capacity_kg")
        self._load_kg = value

    @property
    def route(self) -> deque[Stop]:
        return self._route

    @route.setter
    def route(self, value: deque[Stop] | list[Stop]) -> None:
        if isinstance(value, list):
            self._route = deque(value)
        elif isinstance(value, deque):
            self._route = deque(value)
        else:
            raise ValidationError("Route phải là dạng list hoặc deque chứa các Stop")

    @property
    def free_capacity_kg(self) -> float:
        return self.capacity_kg - self.load_kg

    @property
    def last_node_id(self) -> str:
        if self._route:
            return self._route[-1].node_id
        return self.node_id

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "name": self._name,
            "node_id": self._node_id,
            "capacity_kg": self._capacity_kg,
            "load_kg": self._load_kg,
            "route": [stop.to_dict() for stop in self._route]
        }

    @classmethod
    def from_dict(cls, data: dict) -> Shipper:
        raw_route = data.get("route", [])
        stops_deque = deque([Stop.from_dict(s) for s in raw_route])
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            node_id=data.get("node_id"),
            capacity_kg=data.get("capacity_kg"),
            load_kg=data.get("load_kg", 0.0),
            route=stops_deque
        )
