"""Thực thể bản đồ: địa điểm và đường. Người phụ trách: Quyên."""
from __future__ import annotations

from enum import Enum

from models.base import BaseEntity


class PlaceKind(str, Enum):
    RESTAURANT = "RESTAURANT"  # quán (chỉ có 1)
    JUNCTION = "JUNCTION"      # ngã tư
    HOME = "HOME"              # nhà khách


class Place(BaseEntity):
    """Nút trên bản đồ.

    Trường: id, name, x, y (toạ độ để Plotly vẽ), kind (PlaceKind).
    """

    def __init__(self, id: str, name: str, x: float, y: float,
                 kind: PlaceKind = PlaceKind.JUNCTION) -> None:
        raise NotImplementedError("TODO(Quyên)")


class Road(BaseEntity):
    """Cạnh hai chiều nối hai Place.

    Trường: id, a, b (id hai nút), distance_km (> 0), traffic_factor (>= 1.0,
    kẹt xe thì lớn hơn), blocked (bool, đường bị khóa).
    Validate: trọng số KHÔNG được âm (Dijkstra không chạy với cạnh âm).
    """

    def __init__(self, id: str, a: str, b: str, distance_km: float,
                 traffic_factor: float = 1.0, blocked: bool = False) -> None:
        raise NotImplementedError("TODO(Quyên)")
