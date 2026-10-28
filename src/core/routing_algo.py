"""
[M1] Owner: Lê Trí Tiên
File: src/core/routing_algo.py

Nhiệm vụ:
- Tự cài đặt Dijkstra và A* tìm đường ngắn nhất cho Shipper.
- Dùng CustomMinHeap (src.core.structures) làm hàng đợi ưu tiên; không dùng
  heapq. Chỉ dùng list, dict, set, tuple.
- CustomMinHeap của nhóm: push(item) và pop() -> item, so sánh phần tử theo
  thứ tự tự nhiên. Ở đây phần tử là tuple (f, id_đỉnh): heap so sánh f trước,
  nếu bằng nhau thì so id_đỉnh nên thứ tự duyệt luôn xác định (deterministic).

Ý tưởng: Dijkstra và A* cùng một thuật toán "best-first", chỉ khác khóa ưu
tiên trong heap:
    Dijkstra: f(n) = g(n)            (g = chi phí đã đi từ điểm xuất phát)
    A*:       f(n) = g(n) + h(n)     (h = ước lượng chi phí còn lại tới đích)
Vì vậy cả hai dùng chung hàm _search(); Dijkstra là A* với h(n) = 0.

Interface dùng cho Module 2:
    find_shortest_path(graph, start, goal) -> tuple[list[str], float]
"""

from __future__ import annotations

from typing import Callable, NamedTuple

from src.core.structures import CustomMinHeap
from src.models.graph_node import Graph

INF: float = float("inf")


class RouteResult(NamedTuple):
    """Kết quả một lần tìm đường.

    path:     danh sách id đỉnh từ start tới goal; rỗng nếu không có đường.
    cost:     tổng trọng số của đường đi; INF nếu không có đường.
    expanded: số đỉnh đã được chốt (lấy khỏi heap), dùng để so sánh
              hiệu quả giữa Dijkstra và A*.
    """

    path: list[str]
    cost: float
    expanded: int

    @property
    def found(self) -> bool:
        return bool(self.path)


def _rebuild_path(prev: dict[str, str], start: str, goal: str) -> list[str]:
    """Lần ngược từ goal về start theo dict prev. O(k), k = số đỉnh."""
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def _search(
    graph: Graph,
    start: str,
    goal: str,
    heuristic: Callable[[str], float],
) -> RouteResult:
    """Best-first search dùng min-heap, khóa ưu tiên f = g + h.

    Độ phức tạp: O((V + E) log V).
    - Mỗi cạnh làm tối đa 1 lần push (O(log V)) khi tìm được g nhỏ hơn.
    - Kích thước heap tối đa O(E), log E = O(log V) vì E <= V^2.
    - Heap tự viết không có decrease-key, nên dùng "lazy deletion": cứ push
      mục mới rồi bỏ qua mục cũ (đỉnh đã chốt) khi pop.

    Đúng khi trọng số >= 0 và h consistent (h = 0 cũng consistent).
    """
    graph.get_node(start)  # ValueError nếu đỉnh không tồn tại
    graph.get_node(goal)

    dist: dict[str, float] = {start: 0.0}  # g(n) tốt nhất đã biết
    prev: dict[str, str] = {}  # đỉnh đứng trước trên đường tốt nhất
    closed: set[str] = set()  # đỉnh đã chốt, g(n) là tối ưu
    heap: CustomMinHeap[tuple[float, str]] = CustomMinHeap()
    heap.push((heuristic(start), start))
    expanded = 0

    while not heap.is_empty():
        _, node = heap.pop()  # (f, đỉnh) nhỏ nhất, O(log V)
        if node in closed:  # mục cũ (stale) trong heap -> bỏ qua
            continue
        closed.add(node)
        expanded += 1
        if node == goal:
            path = _rebuild_path(prev, start, goal)
            return RouteResult(path, dist[goal], expanded)

        base = dist[node]
        for neighbor, weight in graph.neighbors(node):
            if neighbor in closed:
                continue
            candidate = base + weight  # nới lỏng cạnh (relaxation)
            if candidate < dist.get(neighbor, INF):
                dist[neighbor] = candidate
                prev[neighbor] = node
                heap.push((candidate + heuristic(neighbor), neighbor))

    return RouteResult([], INF, expanded)  # hết heap mà chưa tới goal


def dijkstra(graph: Graph, start: str, goal: str) -> RouteResult:
    """Dijkstra: A* với h(n) = 0. O((V + E) log V)."""
    return _search(graph, start, goal, lambda _node: 0.0)


def a_star(graph: Graph, start: str, goal: str) -> RouteResult:
    """A* với heuristic là khoảng cách Euclid trên tọa độ (x, y).

    h(n) = k * Euclid(n, goal), k = graph.heuristic_scale() <= 1 nên h luôn
    admissible và consistent -> kết quả tối ưu như Dijkstra, thường duyệt ít
    đỉnh hơn. Trường hợp xấu nhất vẫn O((V + E) log V).
    """
    scale = graph.heuristic_scale()

    def h(node: str) -> float:
        return scale * graph.euclidean_distance(node, goal)

    return _search(graph, start, goal, h)


def find_shortest_path(
    graph: Graph,
    start: str,
    goal: str,
    algorithm: str = "dijkstra",
) -> tuple[list[str], float]:
    """Interface cho Module 2: trả (đường đi, tổng chi phí).

    algorithm: "dijkstra" hoặc "astar".
    Không có đường: ([], inf). start == goal: ([start], 0.0).
    Đỉnh không tồn tại trong bản đồ: ValueError.
    """
    if algorithm == "dijkstra":
        result = dijkstra(graph, start, goal)
    elif algorithm == "astar":
        result = a_star(graph, start, goal)
    else:
        raise ValueError(f"Thuật toán không hỗ trợ: {algorithm!r}")
    return result.path, result.cost


def compare_algorithms(
    graph: Graph, start: str, goal: str
) -> dict[str, RouteResult]:
    """Chạy cả hai thuật toán để so sánh chi phí và số đỉnh đã duyệt."""
    return {
        "dijkstra": dijkstra(graph, start, goal),
        "astar": a_star(graph, start, goal),
    }