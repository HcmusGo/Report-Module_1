"""
[M2] Owner: Đào Đoàn Đỗ Quyên
File: src/core/routing_service.py

Nhiệm vụ:
- Nhận danh sách đỉnh đường đi từ routing_algo (Module 1).
- Ánh xạ từng đỉnh sang tọa độ (x, y).
- Interface đề xuất: path_to_coordinates(path) -> list[tuple[float, float]].
- Chuẩn bị dữ liệu để phần Map trong app.py vẽ lộ trình Shipper.
"""

from __future__ import annotations

from typing import Any, List, Tuple, Dict

from src.core.routing_algo import find_shortest_path
from src.models.graph_node import Graph


def path_to_coordinates(path: List[str], graph: Graph) -> List[Tuple[float, float]]:
    """Ánh xạ danh sách ID đỉnh sang tọa độ (x, y) từ Graph object.

    Độ phức tạp: O(k) với k là số đỉnh trên đường đi.
    """
    coordinates = []
    for node_id in path:
        if graph.has_node(node_id):
            node = graph.get_node(node_id)
            coordinates.append((node.x, node.y))
    return coordinates


def get_map_render_data(graph: Graph, start_id: str, goal_id: str) -> Dict[str, Any]:
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
