"""CRUD bản đồ và khóa / mở đường. Người phụ trách: Bảo."""
from __future__ import annotations

from models.map_entities import Place, PlaceKind, Road
from repositories.map_repository import MapRepository
from services.history import CommandHistory
from services.road_network import RoadNetwork


class MapService:
    """Giữ RoadNetwork đồng bộ với map.json: sửa đồ thị xong thì lưu qua MapRepository.

    Luật gợi ý: chỉ có đúng 1 Place kind RESTAURANT, không xóa Place còn đường nối,
    distance_km > 0, traffic_factor >= 1.0 (không được âm).
    """

    def __init__(self, repo: MapRepository, network: RoadNetwork, history: CommandHistory) -> None:
        self._repo, self._network, self._history = repo, network, history

    def load(self) -> None:
        """Đọc map.json và dựng RoadNetwork. Gọi một lần khi khởi động."""
        raise NotImplementedError("TODO(Bảo)")

    def get_network(self) -> RoadNetwork:
        raise NotImplementedError("TODO(Bảo)")

    def restaurant_node(self) -> str:
        """id của Place kind RESTAURANT."""
        raise NotImplementedError("TODO(Bảo)")

    def list_places(self, kind: PlaceKind | None = None) -> list[Place]:
        raise NotImplementedError("TODO(Bảo)")

    def add_place(self, name: str, x: float, y: float, kind: PlaceKind = PlaceKind.JUNCTION) -> Place:
        raise NotImplementedError("TODO(Bảo)")

    def update_place(self, place_id: str, **changes) -> Place:
        raise NotImplementedError("TODO(Bảo)")

    def delete_place(self, place_id: str) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def list_roads(self) -> list[Road]:
        raise NotImplementedError("TODO(Bảo)")

    def add_road(self, a: str, b: str, distance_km: float, traffic_factor: float = 1.0) -> Road:
        raise NotImplementedError("TODO(Bảo)")

    def update_road(self, road_id: str, **changes) -> Road:
        raise NotImplementedError("TODO(Bảo)")

    def delete_road(self, road_id: str) -> None:
        raise NotImplementedError("TODO(Bảo)")

    def set_road_blocked(self, road_id: str, blocked: bool) -> None:
        """Dùng SetRoadBlockedCmd qua self._history.execute() để Undo được."""
        raise NotImplementedError("TODO(Bảo)")
