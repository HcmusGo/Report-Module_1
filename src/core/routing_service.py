"""
[M2] Owner: Đào Đoàn Đỗ Quyên
File: src/core/routing_service.py

Nhiệm vụ:
- Định nghĩa các hằng số và ngoại lệ cho bản đồ và tìm đường.
- Nạp bản đồ và xử lý 6 trường hợp lỗi dữ liệu bản đồ.
- Kiểm tra tính hợp lệ của điểm giao hàng.
- Tìm đường đơn lẻ và lập kế hoạch gom chuyến (Batch Route) theo thuật toán Nearest-Neighbor.
- So sánh hiệu năng giữa thuật toán Dijkstra và A*.
- Chuẩn bị dữ liệu hiển thị bản đồ phục vụ giao diện Streamlit / Altair.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

from src.core.routing_algo import a_star, dijkstra, find_shortest_path
from src.core.storage import _resolve_path, load_json
from src.models.graph_node import Graph

RESTAURANT_NODE_ID: str = "RESTAURANT"
MAP_PATH: str = "data/map_graph.json"


class MapDataError(Exception):
    """Ngoại lệ khi nạp hoặc xác thực dữ liệu bản đồ."""

    pass


class SingleRoute(NamedTuple):
    """Kết quả tìm đường cho một đơn hàng từ Quán tới điểm giao."""

    delivery_node_id: str
    path: list[str]
    coords: list[tuple[float, float]]
    cost: float
    expanded: int


class RouteLeg(NamedTuple):
    """Một chặng trong lộ trình gom chuyến."""

    start: str
    end: str
    path: list[str]
    cost: float


class BatchRoute(NamedTuple):
    """Lộ trình gom chuyến cho nhiều đơn hàng."""

    visit_order: list[str]
    legs: list[RouteLeg]
    full_path: list[str]
    coords: list[tuple[float, float]]
    total_cost: float
    expanded_total: int
    algorithm: str


def load_map_graph(path: str = MAP_PATH) -> Graph:
    """Nạp bản đồ từ file JSON và phát hiện 6 lỗi cấu trúc / dữ liệu bản đồ.

    Các trường hợp lỗi:
    (a) File không tồn tại -> MapDataError
    (b) File rỗng -> MapDataError
    (c) JSON sai cú pháp (sau khi load_json trả về {} và tồn tại file .bak) -> MapDataError
    (d) Thiếu trường 'nodes' hoặc danh sách 'nodes' rỗng -> MapDataError
    (e) Thiếu đỉnh xuất phát của quán RESTAURANT_NODE_ID -> MapDataError
    (f) Graph.from_dict ném ValueError -> bọc lại thành MapDataError
    """
    p = Path(path)
    resolved = _resolve_path(path)

    # Kiểm tra sự tồn tại của file trước khi load_json
    file_existed = p.is_file() or resolved.is_file()

    # Kiểm tra file rỗng trước khi load_json
    if file_existed:
        actual_path = p if p.is_file() else resolved
        try:
            content = actual_path.read_text(encoding="utf-8")
            if not content.strip():
                raise MapDataError(f"File bản đồ rỗng: {path}")
        except UnicodeDecodeError:
            pass

    # Đọc dữ liệu JSON
    data = load_json(path, default={})

    # (c) JSON sai cú pháp: load_json trả về {} và tồn tại file .bak
    bak_orig = p.with_name(f"{p.name}.bak")
    bak_resolved = resolved.with_name(f"{resolved.name}.bak")
    if (bak_orig.is_file() or bak_resolved.is_file()) and data == {}:
        raise MapDataError(
            f"{p.name} bị sai cú pháp và đã được đổi tên thành {p.name}.bak; "
            "hãy sửa file .bak rồi đổi tên lại"
        )

    # (a) File không tồn tại
    if not file_existed:
        raise MapDataError(f"File bản đồ không tồn tại: {path}")

    # (d) Thiếu 'nodes' hoặc không có đỉnh nào
    if not isinstance(data, dict) or "nodes" not in data or not data["nodes"]:
        raise MapDataError("Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.")

    # (e) Thiếu đỉnh RESTAURANT_NODE_ID
    raw_nodes = data["nodes"]
    has_restaurant = False
    if isinstance(raw_nodes, dict):
        has_restaurant = RESTAURANT_NODE_ID in raw_nodes
    elif isinstance(raw_nodes, (list, tuple)):
        has_restaurant = any(
            isinstance(item, dict) and str(item.get("id", "")).strip() == RESTAURANT_NODE_ID
            for item in raw_nodes
        )
    if not has_restaurant:
        raise MapDataError(
            f"Bản đồ thiếu đỉnh xuất phát của quán ({RESTAURANT_NODE_ID})."
        )

    # (f) Graph.from_dict ném ValueError
    try:
        return Graph.from_dict(data)
    except ValueError as err:
        raise MapDataError(f"Lỗi cấu trúc đồ thị bản đồ: {err}") from err


def is_valid_delivery_node(graph: Graph, node_id: str) -> bool:
    """Kiểm tra một đỉnh có phải là điểm giao hàng hợp lệ hay không.

    Điều kiện:
    - node_id là chuỗi không rỗng và khác RESTAURANT_NODE_ID.
    - Đỉnh tồn tại trong đồ thị.
    - Đỉnh RESTAURANT_NODE_ID tồn tại trong đồ thị.
    - Có đường đi hợp lệ từ Quán tới đỉnh (dijkstra().found is True).
    """
    if not isinstance(node_id, str):
        return False
    clean_id = node_id.strip()
    if not clean_id or clean_id == RESTAURANT_NODE_ID:
        return False
    if not graph.has_node(clean_id) or not graph.has_node(RESTAURANT_NODE_ID):
        return False
    try:
        route = dijkstra(graph, RESTAURANT_NODE_ID, clean_id)
        return route.found
    except (ValueError, KeyError):
        return False


def route_single_order(
    graph: Graph, delivery_node_id: str, algorithm: str = "dijkstra"
) -> SingleRoute:
    """Tìm đường ngắn nhất từ Quán đến một điểm giao hàng đơn lẻ.

    Args:
        graph: Đồ thị bản đồ giao hàng.
        delivery_node_id: ID đỉnh đích nhận hàng.
        algorithm: 'dijkstra' hoặc 'astar'.

    Returns:
        SingleRoute chứa thông tin đường đi, tọa độ, chi phí và số đỉnh đã duyệt.

    Raises:
        ValueError: Nếu điểm giao không hợp lệ, không có đường đi, hoặc thuật toán sai.
    """
    if not is_valid_delivery_node(graph, delivery_node_id):
        raise ValueError(
            f"Điểm giao không hợp lệ hoặc không có đường đi: {delivery_node_id!r}"
        )

    algo = algorithm.lower().strip()
    if algo == "dijkstra":
        result = dijkstra(graph, RESTAURANT_NODE_ID, delivery_node_id)
    elif algo in ("astar", "a_star"):
        result = a_star(graph, RESTAURANT_NODE_ID, delivery_node_id)
    else:
        raise ValueError(f"Thuật toán không hỗ trợ: {algorithm!r}")

    if not result.found:
        raise ValueError(
            f"Không tìm thấy đường tới điểm giao: {delivery_node_id!r}"
        )

    coords = path_to_coordinates(result.path, graph)
    return SingleRoute(
        delivery_node_id=delivery_node_id,
        path=result.path,
        coords=coords,
        cost=result.cost,
        expanded=result.expanded,
    )


def plan_batch_route(
    graph: Graph, delivery_node_ids: list[str], algorithm: str = "dijkstra"
) -> BatchRoute:
    """Lập kế hoạch gom chuyến giao hàng theo giải thuật tham lam Nearest-Neighbor.

    Độ phức tạp: O(k^2 (V+E) log V) với k là số lượng điểm giao hàng độc nhất.
    Tại mỗi bước, từ vị trí hiện tại duyệt qua tất cả các điểm chưa giao còn lại,
    chọn điểm có chi phí nhỏ nhất (nếu bằng nhau chọn id nhỏ hơn theo thứ tự từ điển),
    di chuyển tới điểm đó và tiếp tục cho đến khi giao hết. Không quay về Quán.

    Args:
        graph: Đồ thị bản đồ giao hàng.
        delivery_node_ids: Danh sách ID các điểm cần giao hàng.
        algorithm: 'dijkstra' hoặc 'astar'.

    Returns:
        BatchRoute chứa thứ tự thăm, các chặng, lộ trình đầy đủ và tổng chi phí.

    Raises:
        ValueError: Nếu danh sách rỗng, có điểm không hợp lệ, hoặc thuật toán không hỗ trợ.
    """
    if not delivery_node_ids:
        raise ValueError("Danh sách điểm giao hàng rỗng.")

    algo = algorithm.lower().strip()
    if algo == "dijkstra":
        search_fn = dijkstra
    elif algo in ("astar", "a_star"):
        search_fn = a_star
    else:
        raise ValueError(f"Thuật toán không hỗ trợ: {algorithm!r}")

    # Lọc trùng điểm giao nhưng giữ nguyên thứ tự xuất hiện ban đầu
    unique_nodes: list[str] = []
    seen: set[str] = set()
    for nid in delivery_node_ids:
        if not isinstance(nid, str) or not nid.strip():
            raise ValueError(f"Điểm giao không hợp lệ: {nid!r}")
        clean_id = nid.strip()
        if not is_valid_delivery_node(graph, clean_id):
            raise ValueError(
                f"Điểm giao không hợp lệ hoặc không có đường đi: {clean_id!r}"
            )
        if clean_id not in seen:
            seen.add(clean_id)
            unique_nodes.append(clean_id)

    if not unique_nodes:
        raise ValueError("Danh sách điểm giao hàng rỗng sau khi lọc trùng.")

    current_node = RESTAURANT_NODE_ID
    unvisited = list(unique_nodes)
    visit_order: list[str] = []
    legs: list[RouteLeg] = []
    expanded_total = 0

    while unvisited:
        best_cand: str | None = None
        best_cost: float = float("inf")
        best_res = None

        for cand in unvisited:
            res = search_fn(graph, current_node, cand)
            if not res.found:
                raise ValueError(
                    f"Không tìm thấy đường từ {current_node!r} tới {cand!r}"
                )
            # Chọn điểm có cost nhỏ nhất; nếu hòa chọn id nhỏ hơn theo thứ tự từ điển
            if best_cand is None or (res.cost, cand) < (best_cost, best_cand):
                best_cand = cand
                best_cost = res.cost
                best_res = res

        assert best_cand is not None and best_res is not None
        legs.append(
            RouteLeg(
                start=current_node,
                end=best_cand,
                path=best_res.path,
                cost=best_res.cost,
            )
        )
        visit_order.append(best_cand)
        expanded_total += best_res.expanded
        unvisited.remove(best_cand)
        current_node = best_cand

    # Nối full_path: path chặng đầu + path các chặng sau bỏ đỉnh đầu
    full_path: list[str] = []
    for i, leg in enumerate(legs):
        if i == 0:
            full_path.extend(leg.path)
        else:
            full_path.extend(leg.path[1:])

    coords = path_to_coordinates(full_path, graph)
    total_cost = sum(leg.cost for leg in legs)

    return BatchRoute(
        visit_order=visit_order,
        legs=legs,
        full_path=full_path,
        coords=coords,
        total_cost=total_cost,
        expanded_total=expanded_total,
        algorithm="dijkstra" if algo == "dijkstra" else "astar",
    )


def compare_trip_algorithms(
    graph: Graph, delivery_node_ids: list[str]
) -> dict[str, BatchRoute]:
    """So sánh kết quả gom chuyến giữa thuật toán Dijkstra và A*.

    Args:
        graph: Đồ thị bản đồ.
        delivery_node_ids: Danh sách ID các điểm cần giao.

    Returns:
        Dict có hai khóa 'dijkstra' và 'astar', giá trị là BatchRoute tương ứng.
    """
    return {
        "dijkstra": plan_batch_route(graph, delivery_node_ids, algorithm="dijkstra"),
        "astar": plan_batch_route(graph, delivery_node_ids, algorithm="astar"),
    }


def build_map_figure_data(
    graph: Graph, full_path: list[str] | None = None
) -> dict[str, Any]:
    """Chuẩn bị dữ liệu hiển thị bản đồ cho Altair hoặc giao diện Streamlit.

    Args:
        graph: Đồ thị bản đồ giao hàng.
        full_path: Lộ trình đầy đủ (danh sách ID đỉnh) cần đánh dấu, hoặc None.

    Returns:
        Dict gồm 3 danh sách:
        - 'nodes': [{'id': ..., 'name': ..., 'x': ..., 'y': ..., 'on_route': bool}]
        - 'edges': [{'x': ..., 'y': ..., 'x2': ..., 'y2': ...}] (mỗi cạnh vô hướng 1 lần)
        - 'route': [{'step': int, 'node_id': ..., 'x': ..., 'y': ...}]
    """
    path_set = set(full_path) if full_path else set()

    nodes_data = [
        {
            "id": node.id,
            "name": node.name,
            "x": node.x,
            "y": node.y,
            "on_route": bool(node.id in path_set),
        }
        for node in graph.nodes
    ]

    seen_edges: set[tuple[str, str]] = set()
    edges_data = []
    for u, v, _ in graph.edges():
        pair = (min(u, v), max(u, v))
        if pair not in seen_edges and u != v:
            seen_edges.add(pair)
            u_node = graph.get_node(pair[0])
            v_node = graph.get_node(pair[1])
            edges_data.append(
                {
                    "x": u_node.x,
                    "y": u_node.y,
                    "x2": v_node.x,
                    "y2": v_node.y,
                }
            )

    route_data = []
    if full_path:
        for step, node_id in enumerate(full_path):
            if graph.has_node(node_id):
                node = graph.get_node(node_id)
                route_data.append(
                    {
                        "step": step,
                        "node_id": node_id,
                        "x": node.x,
                        "y": node.y,
                    }
                )

    return {
        "nodes": nodes_data,
        "edges": edges_data,
        "route": route_data,
    }


def path_to_coordinates(
    path: list[str], graph: Graph
) -> list[tuple[float, float]]:
    """Ánh xạ danh sách ID đỉnh sang tọa độ (x, y) từ Graph object.

    Độ phức tạp: O(k) với k là số đỉnh trên đường đi.
    """
    coordinates = []
    for node_id in path:
        if graph.has_node(node_id):
            node = graph.get_node(node_id)
            coordinates.append((node.x, node.y))
    return coordinates


def get_map_render_data(
    graph: Graph, start_id: str, goal_id: str
) -> dict[str, Any]:
    """Tính đường đi ngắn nhất và trả về dữ liệu để render trên giao diện.

    Độ phức tạp: O((V + E) log V) theo thuật toán Dijkstra/A*.
    """
    path, total_distance = find_shortest_path(graph, start_id, goal_id)
    path_coords = path_to_coordinates(path, graph)

    return {
        "path": path,
        "path_coords": path_coords,
        "total_distance": total_distance,
    }
