"""Đồ thị bản đồ. Người phụ trách: Bảo."""
from __future__ import annotations

from collections.abc import Iterator

from models.map_entities import Place, Road


class RoadNetwork:
    """Danh sách kề: dict[node_id, list[(neighbor_id, road)]], đường hai chiều.

    Trọng số = thời gian (phút) = distance_km / AVG_SPEED_KMH * 60 * traffic_factor.
    Đường blocked=True bị bỏ qua khi duyệt.
    """

    def __init__(self) -> None:
        self._adj: dict[str, list[tuple[str, Road]]] = {}
        self._places: dict[str, Place] = {}
        self._roads: dict[str, Road] = {}

    def load(self, places: list[Place], roads: list[Road]) -> None:
        """Dựng lại đồ thị từ dữ liệu, thay thế đồ thị cũ."""
        raise NotImplementedError("TODO(Bảo)")

    def has_node(self, node_id: str) -> bool:
        raise NotImplementedError("TODO(Bảo)")

    def nodes(self) -> list[str]:
        raise NotImplementedError("TODO(Bảo)")

    def neighbors(self, node_id: str) -> Iterator[tuple[str, float]]:
        """Sinh (id nút kề, thời gian phút), bỏ qua đường đang khóa. Dijkstra / BFS dùng hàm này."""
        raise NotImplementedError("TODO(Bảo)")

    def travel_minutes(self, road: Road) -> float:
        """Đổi một Road sang phút. Phải >= 0."""
        raise NotImplementedError("TODO(Bảo)")

    def set_blocked(self, road_id: str, blocked: bool) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def add_place(self, place: Place) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def add_road(self, road: Road) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def remove_road(self, road_id: str) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def remove_place(self, place_id: str) -> None:
        raise NotImplementedError("TODO(Bảo)")
