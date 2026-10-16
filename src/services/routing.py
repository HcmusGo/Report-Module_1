"""Đồ thị bản đồ và thuật toán tìm đường. Người phụ trách: Bảo."""
from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from exceptions import ValidationError
from models.map_entities import Place, Road
from repositories.base_repository import Repository

Weight = Literal["time", "distance"]   # tìm đường nhanh nhất (phút) hay ngắn nhất (km)

_INF = float("inf")


def _check_weight(by: str) -> None:
    if by not in ("time", "distance"):
        raise ValidationError(
            f"Tiêu chí tìm đường không hợp lệ: {by!r} (chỉ nhận 'time' hoặc 'distance')")


def _edge_weight(road: Road, by: str) -> float:
    """Trọng số cạnh theo tiêu chí: 'time' -> road.minutes, 'distance' -> road.distance_km."""
    return road.minutes if by == "time" else road.distance_km


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

    def _graph(self) -> dict[str, list[tuple[str, Road]]]:
        """Trả danh sách kề, dựng ở lần gọi đầu tiên (lazy) rồi dùng lại."""
        if self._adj is None:
            adj: dict[str, list[tuple[str, Road]]] = {}
            # Mọi Place đều là nút, kể cả nút cô lập (không có đường nào).
            for place in self._places.get_all():
                adj.setdefault(place.id, [])
            # Road là cạnh hai chiều: thêm vào cả hai đầu.
            for road in self._roads.get_all():
                adj.setdefault(road.a, []).append((road.b, road))
                adj.setdefault(road.b, []).append((road.a, road))
            self._adj = adj
        return self._adj

    def has_node(self, node_id: str) -> bool:
        return node_id in self._graph()

    def neighbors(self, node_id: str) -> list[tuple[str, Road]]:
        """(id nút kề, Road). Router dùng road.minutes hoặc road.distance_km làm trọng số."""
        # Trả bản sao để bên gọi không làm hỏng danh sách kề; nút lạ -> danh sách rỗng.
        return list(self._graph().get(node_id, ()))


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

    @staticmethod
    def _run(network: RoadNetwork, src: str, by: str, dst: str | None = None
             ) -> tuple[dict[str, float], dict[str, tuple[str, Road]], int]:
        """Lõi Dijkstra. Trả (dist, prev, nodes_visited).

        prev[v] = (u, road) nghĩa là đường tốt nhất tới v đi qua cạnh road từ u.
        Nếu có dst thì dừng sớm ngay khi dst được chốt (lấy ra khỏi heap).
        """
        dist: dict[str, float] = {src: 0.0}
        prev: dict[str, tuple[str, Road]] = {}
        heap: list[tuple[float, str]] = [(0.0, src)]
        visited = 0
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue  # bản ghi cũ (lazy deletion)
            visited += 1
            if u == dst:
                break
            for v, road in network.neighbors(u):
                nd = d + _edge_weight(road, by)
                if nd < dist.get(v, _INF):
                    dist[v] = nd
                    prev[v] = (u, road)
                    heapq.heappush(heap, (nd, v))
        return dist, prev, visited

    def shortest_path(self, network: RoadNetwork, src: str, dst: str,
                      by: Weight = "time") -> PathResult:
        _check_weight(by)
        if not network.has_node(src) or not network.has_node(dst):
            return PathResult.not_found(nodes_visited=0)

        dist, prev, visited = self._run(network, src, by, dst)
        if dst not in dist:
            return PathResult.not_found(nodes_visited=visited)

        # Truy vết ngược dst -> src, cộng dồn CẢ phút lẫn km bất kể tối ưu theo gì.
        path = [dst]
        minutes = 0.0
        distance_km = 0.0
        node = dst
        while node != src:
            parent, road = prev[node]
            minutes += road.minutes
            distance_km += road.distance_km
            path.append(parent)
            node = parent
        path.reverse()
        return PathResult(path=path, minutes=minutes, distance_km=distance_km,
                          nodes_visited=visited)

    def distances_from(self, network: RoadNetwork, src: str, by: Weight = "time") -> dict[str, float]:
        _check_weight(by)
        if not network.has_node(src):
            return {}
        dist, _, _ = self._run(network, src, by)
        return dist
