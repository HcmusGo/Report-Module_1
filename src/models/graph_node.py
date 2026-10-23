"""
[M1] Owner: Lê Trí Tiên
File: src/models/graph_node.py

Nhiệm vụ:
- GraphNode: đỉnh của bản đồ (id, tên, tọa độ x, y), kế thừa BaseEntity.
- Graph: bản đồ giao hàng biểu diễn bằng danh sách kề
  dict[str, list[tuple[str, float]]]. Chỉ dùng list, dict, set, tuple.

Dùng BaseEntity (src/models/base.py): id được strip và kiểm tra ở lớp cha,
to_dict() mở rộng từ super().to_dict(). GraphNode khóa id (chỉ đọc) vì Graph
dùng id làm khóa tra cứu, đổi id sau khi đã thêm vào Graph sẽ làm lệch khóa.

Định dạng data/map_graph.json mà Graph.from_dict() đọc được:
    {
      "nodes": {"A": {"name": "Ngã tư A", "x": 2, "y": 1}, ...},
      "edges": [["A", "B", 2.2], ...]
    }
Ngoài ra "nodes" có thể là list các dict có khóa "id", và mỗi edge có thể
là dict với khóa from/to/weight. Đường mặc định là hai chiều.
"""

from __future__ import annotations

import math
from typing import Any

from src.models.base import BaseEntity

_EDGE_FROM_KEYS = ("from", "source", "u", "a")
_EDGE_TO_KEYS = ("to", "target", "v", "b")
_EDGE_WEIGHT_KEYS = ("weight", "distance", "distance_km", "cost", "w")


def _to_number(value: Any, label: str) -> float:
    """Ép về float hữu hạn; từ chối bool, chuỗi, NaN và vô cực. O(1)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} phải là số, nhận được {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} phải là số hữu hạn, nhận được {value!r}")
    return number


def _pick(data: dict[str, Any], keys: tuple[str, ...], label: str) -> Any:
    """Lấy giá trị của khóa đầu tiên có trong data."""
    for key in keys:
        if key in data:
            return data[key]
    raise ValueError(f"Cạnh thiếu trường {label} (một trong {keys}): {data!r}")


def _parse_edge(edge: Any) -> tuple[str, str, float]:
    """Đọc một cạnh dạng [u, v, w] hoặc dict thành (u, v, w)."""
    if isinstance(edge, dict):
        source = _pick(edge, _EDGE_FROM_KEYS, "điểm đầu")
        target = _pick(edge, _EDGE_TO_KEYS, "điểm cuối")
        weight = _pick(edge, _EDGE_WEIGHT_KEYS, "trọng số")
        return (
            str(source).strip(),
            str(target).strip(),
            _to_number(weight, "Trọng số cạnh"),
        )
    if isinstance(edge, (list, tuple)) and len(edge) == 3:
        return (
            str(edge[0]).strip(),
            str(edge[1]).strip(),
            _to_number(edge[2], "Trọng số cạnh"),
        )
    raise ValueError(f"Định dạng cạnh không hợp lệ: {edge!r}")


class GraphNode(BaseEntity):
    """Một đỉnh trên bản đồ: địa điểm có tên và tọa độ (x, y)."""

    def __init__(self, node_id: str, name: str, x: float, y: float) -> None:
        super().__init__(node_id)
        self._name: str = ""
        self._x: float = 0.0
        self._y: float = 0.0
        self.name = name
        self.x = x
        self.y = y

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, new_id: str) -> None:
        """Chặn đổi id: Graph dùng id làm khóa nên id phải cố định."""
        raise AttributeError("id của GraphNode không được thay đổi")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Tên địa điểm không được rỗng")
        self._name = value.strip()

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = _to_number(value, "Tọa độ x")

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = _to_number(value, "Tọa độ y")

    def distance_to(self, other: GraphNode) -> float:
        """Khoảng cách Euclid tới đỉnh khác. O(1)."""
        return math.hypot(self._x - other._x, self._y - other._y)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()  # {"id": ...} từ BaseEntity
        data.update({"name": self._name, "x": self._x, "y": self._y})
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        """Khởi tạo từ dict JSON.

        Phải override: BaseEntity.from_dict gọi cls(id=...) nên không dùng
        được cho GraphNode có thêm name, x, y.
        """
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu đầu vào phải là dictionary.")
        for key in ("id", "name", "x", "y"):
            if key not in data:
                raise ValueError(f"Dữ liệu thiếu trường {key!r}.")
        return cls(str(data["id"]), data["name"], data["x"], data["y"])

    def __repr__(self) -> str:
        return f"GraphNode({self.id!r}, {self._name!r}, {self._x}, {self._y})"


class Graph:
    """Bản đồ giao hàng: danh sách kề + bảng tra đỉnh theo id.

    _nodes: id -> GraphNode                       (tra cứu O(1))
    _adj:   id -> list[(id_đỉnh_kề, trọng_số)]    (danh sách kề)

    Bộ nhớ O(V + E), tốt hơn ma trận kề O(V^2) vì bản đồ đường phố thưa.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._adj: dict[str, list[tuple[str, float]]] = {}
        self._scale: float | None = None  # cache của heuristic_scale()

    # ------------------------------------------------------------ truy vấn
    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_id: object) -> bool:
        return node_id in self._nodes

    @property
    def node_ids(self) -> list[str]:
        return list(self._nodes)

    @property
    def nodes(self) -> list[GraphNode]:
        return list(self._nodes.values())

    def has_node(self, node_id: str) -> bool:
        """O(1)."""
        return node_id in self._nodes

    def get_node(self, node_id: str) -> GraphNode:
        """Lấy đỉnh theo id; id không tồn tại thì ValueError. O(1)."""
        node = self._nodes.get(node_id)
        if node is None:
            raise ValueError(f"Đỉnh không tồn tại trong bản đồ: {node_id!r}")
        return node

    def neighbors(self, node_id: str) -> list[tuple[str, float]]:
        """Các đỉnh kề và trọng số cạnh tương ứng. O(deg)."""
        self.get_node(node_id)
        return list(self._adj[node_id])

    def edges(self) -> list[tuple[str, str, float]]:
        """Mọi cạnh có hướng (u, v, w); đường hai chiều xuất hiện 2 lần."""
        return [(u, v, w) for u, arcs in self._adj.items() for v, w in arcs]

    def euclidean_distance(self, a: str, b: str) -> float:
        """Khoảng cách Euclid giữa hai đỉnh theo id. O(1)."""
        return self.get_node(a).distance_to(self.get_node(b))

    def heuristic_scale(self) -> float:
        """Hệ số co k <= 1 để h(n) = k * Euclid(n, đích) luôn hợp lệ cho A*.

        Với mọi cạnh (u, v, w) cần k * Euclid(u, v) <= w. Lấy
        k = min(1, min w / Euclid(u, v)) thì h vừa admissible (không ước
        lượng quá chi phí thật) vừa consistent (theo bất đẳng thức tam giác),
        nên A* luôn ra đường tối ưu dù trọng số không bằng đúng khoảng cách.
        Tính một lần O(E) rồi cache.
        """
        if self._scale is None:
            scale = 1.0
            for u, v, w in self.edges():
                dist = self.euclidean_distance(u, v)
                if dist > 0.0:
                    scale = min(scale, w / dist)
            self._scale = scale
        return self._scale

    # ---------------------------------------------------------- dựng đồ thị
    def add_node(self, node: GraphNode) -> None:
        """Thêm đỉnh; trùng id thì ValueError. O(1)."""
        if node.id in self._nodes:
            raise ValueError(f"Đỉnh bị trùng id: {node.id!r}")
        self._nodes[node.id] = node
        self._adj[node.id] = []
        self._scale = None

    def add_edge(
        self, u: str, v: str, weight: float, bidirectional: bool = True
    ) -> None:
        """Thêm cạnh u -> v (và v -> u nếu hai chiều). O(1).

        Trọng số phải >= 0 vì Dijkstra/A* không đúng với cạnh âm.
        """
        self.get_node(u)
        self.get_node(v)
        cost = _to_number(weight, "Trọng số cạnh")
        if cost < 0:
            raise ValueError(f"Trọng số cạnh không được âm: {cost}")
        self._adj[u].append((v, cost))
        if bidirectional and u != v:
            self._adj[v].append((u, cost))
        self._scale = None

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], bidirectional: bool = True
    ) -> Graph:
        """Dựng Graph từ dữ liệu đọc từ map_graph.json. O(V + E).

        data["directed"] = True sẽ ghi đè bidirectional (đường một chiều).
        """
        graph = cls()
        raw_nodes = data["nodes"]
        if isinstance(raw_nodes, dict):
            entries = list(raw_nodes.items())
        else:
            entries = [(item["id"], item) for item in raw_nodes]
        for raw_id, info in entries:
            node_id = str(raw_id).strip()
            name = info.get("name") or node_id
            graph.add_node(GraphNode(node_id, name, info["x"], info["y"]))

        two_way = bidirectional and not data.get("directed", False)
        for edge in data["edges"]:
            u, v, weight = _parse_edge(edge)
            graph.add_edge(u, v, weight, two_way)
        return graph