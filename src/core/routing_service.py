from typing import List, Tuple, Dict, Any
from src.core.routing_algo import find_shortest_path


def path_to_coordinates(path: List[str], graph_nodes: Dict[str, Any]) -> List[Tuple[float, float]]:
    coordinates = []
    for node_id in path:
        if node_id in graph_nodes:
            node = graph_nodes[node_id]
            coordinates.append((node.x, node.y))
    return coordinates


def get_map_render_data(graph_data: Dict[str, Any], start_id: str, goal_id: str) -> Dict[str, Any]:
    path, total_distance = find_shortest_path(graph_data, start_id, goal_id)
    path_coords = path_to_coordinates(path, graph_data)
    
    return {
        "path": path,
        "path_coords": path_coords,
        "total_distance": total_distance
    }
