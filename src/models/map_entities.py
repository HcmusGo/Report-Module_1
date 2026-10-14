"""Bản đồ: địa điểm và đường. Dữ liệu khởi tạo sẵn, UI chỉ xem. Người phụ trách: Quyên."""
from __future__ import annotations

from enum import Enum

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
        raise NotImplementedError("TODO(Quyên)")


class Road(BaseEntity):
    """Cạnh hai chiều nối hai Place.

    Trường: id, a, b (id hai nút), distance_km (> 0), traffic (TrafficLevel).
    Property `minutes` = distance_km / config.TRAFFIC_SPEED_KMH[traffic] * 60, luôn >= 0
    (Dijkstra không chạy với trọng số âm).
    """

    def __init__(self, id: str, a: str, b: str, distance_km: float,
                 traffic: TrafficLevel = TrafficLevel.MEDIUM) -> None:
        raise NotImplementedError("TODO(Quyên)")

    @property
    def minutes(self) -> float:
        raise NotImplementedError("TODO(Quyên)")
