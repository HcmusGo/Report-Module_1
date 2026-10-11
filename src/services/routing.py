"""Thuật toán tìm đường: Strategy pattern. Người phụ trách: Bảo."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from services.road_network import RoadNetwork


@dataclass(frozen=True)
class PathResult:
    path: list[str] = field(default_factory=list)   # danh sách id nút từ src đến dst
    cost: float = 0.0                               # tổng thời gian (phút)
    nodes_visited: int = 0                          # số nút đã duyệt, để so sánh thuật toán

    @property
    def found(self) -> bool:
        return bool(self.path)

    @classmethod
    def not_found(cls, nodes_visited: int = 0) -> "PathResult":
        return cls(path=[], cost=float("inf"), nodes_visited=nodes_visited)


class Router(ABC):
    name: str = "router"

    @abstractmethod
    def shortest_path(self, network: RoadNetwork, src: str, dst: str) -> PathResult:
        """Đường đi từ src đến dst. Không có đường thì trả PathResult.not_found()."""

    @abstractmethod
    def distances_from(self, network: RoadNetwork, src: str) -> dict[str, float]:
        """Thời gian ngắn nhất từ src đến MỌI nút đến được (chạy một lần)."""


class DijkstraRouter(Router):
    """heapq + dict dist / prev, bỏ bản ghi cũ trong heap (lazy deletion).
    Nút không đến được thì không có trong dist (dùng dist.get(x, inf)).
    Độ phức tạp O((V + E) log V)."""

    name = "Dijkstra"

    def shortest_path(self, network: RoadNetwork, src: str, dst: str) -> PathResult:
        raise NotImplementedError("TODO(Bảo)")

    def distances_from(self, network: RoadNetwork, src: str) -> dict[str, float]:
        raise NotImplementedError("TODO(Bảo)")


class BFSRouter(Router):
    """Đối chứng: tìm đường ÍT CẠNH nhất bằng deque + set visited, bỏ qua trọng số.
    Dùng để chứng minh BFS cho kết quả sai khi các đường có độ dài khác nhau.
    cost vẫn là tổng thời gian của đường BFS tìm được, để so với Dijkstra."""

    name = "BFS"

    def shortest_path(self, network: RoadNetwork, src: str, dst: str) -> PathResult:
        raise NotImplementedError("TODO(Bảo)")

    def distances_from(self, network: RoadNetwork, src: str) -> dict[str, float]:
        raise NotImplementedError("TODO(Bảo)")
