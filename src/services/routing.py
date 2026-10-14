"""Đồ thị bản đồ và thuật toán tìm đường. Người phụ trách: Bảo."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from models.map_entities import Place, Road
from repositories.base_repository import Repository

Weight = Literal["time", "distance"]   # tìm đường nhanh nhất (phút) hay ngắn nhất (km)


@dataclass(frozen=True)
class PathResult:
    path: list[str] = field(default_factory=list)   # id nút từ src đến dst
    minutes: float = 0.0                            # tổng thời gian của đường này
    distance_km: float = 0.0                        # tổng quãng đường của đường này
    nodes_visited: int = 0

    @property
    def found(self) -> bool:
        return bool(self.path)

    @classmethod
    def not_found(cls, nodes_visited: int = 0) -> "PathResult":
        return cls(path=[], minutes=float("inf"), distance_km=float("inf"),
                   nodes_visited=nodes_visited)


class RoadNetwork:
    """Danh sách kề hai chiều: dict[node_id, list[(neighbor_id, Road)]].

    Nhận Repository qua constructor và dựng danh sách kề LẦN ĐẦU cần dùng (lazy), vì bản đồ
    chỉ đọc, nạp sẵn từ places.json và roads.json.
    """

    def __init__(self, places: Repository[Place], roads: Repository[Road]) -> None:
        self._places, self._roads = places, roads
        self._adj: dict[str, list[tuple[str, Road]]] | None = None

    def has_node(self, node_id: str) -> bool:
        raise NotImplementedError("TODO(Bảo)")

    def neighbors(self, node_id: str) -> list[tuple[str, Road]]:
        """(id nút kề, Road). Router dùng road.minutes hoặc road.distance_km làm trọng số."""
        raise NotImplementedError("TODO(Bảo)")


class Router(ABC):
    @abstractmethod
    def shortest_path(self, network: RoadNetwork, src: str, dst: str,
                      by: Weight = "time") -> PathResult:
        """Đường đi từ src đến dst. Không có đường thì trả PathResult.not_found()."""

    @abstractmethod
    def distances_from(self, network: RoadNetwork, src: str, by: Weight = "time") -> dict[str, float]:
        """Chi phí nhỏ nhất từ src đến mọi nút đến được."""


class DijkstraRouter(Router):
    """heapq + dict dist / prev, bỏ bản ghi cũ trong heap (lazy deletion).
    Nút không có trong dist là không đến được (dùng dist.get(x, inf)).
    Độ phức tạp O((V + E) log V). PathResult phải điền CẢ minutes và distance_km của
    đường tìm được, để so sánh 'nhanh nhất' với 'ngắn nhất' trên cùng một cặp điểm."""

    def shortest_path(self, network: RoadNetwork, src: str, dst: str,
                      by: Weight = "time") -> PathResult:
        raise NotImplementedError("TODO(Bảo)")

    def distances_from(self, network: RoadNetwork, src: str, by: Weight = "time") -> dict[str, float]:
        raise NotImplementedError("TODO(Bảo)")
