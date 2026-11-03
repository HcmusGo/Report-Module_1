## 2026-11-01T03:04:24Z
You are m1_worker, a teamwork_worker subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m1_worker
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONSTRAINTS:
- You ONLY have write ownership of `src/core/routing_service.py`. DO NOT touch any other file.
- NEVER touch any of the 7 core files (including `src/core/routing_algo.py`, `src/models/graph_node.py`, etc.).
- DO NOT import collections/deque, heapq, bisect, queue, networkx.
- Keep line lengths <= 100 characters.

TASK SPECIFICATIONS (Milestone M1: Routing Service):
Implement `src/core/routing_service.py` with:
1. Constants and Exception:
   `RESTAURANT_NODE_ID: str = "RESTAURANT"`
   `MAP_PATH: str = "data/map_graph.json"`
   `class MapDataError(Exception): pass`
2. `load_map_graph(path: str = MAP_PATH) -> Graph`:
   Distinguish all 6 failure modes with explicit Vietnamese error messages (raising MapDataError):
   (a) File does not exist -> `MapDataError(f"File bản đồ không tồn tại: {path}")`
   (b) File is empty (size 0 or only whitespace) -> `MapDataError(f"File bản đồ rỗng: {path}")`
   (c) JSON syntax error: If `load_json` returned `{}` and `<path>.bak` exists (check `Path(path).with_name(f"{Path(path).name}.bak").is_file()`), report:
       `MapDataError(f"{Path(path).name} bị sai cú pháp và đã được đổi tên thành {Path(path).name}.bak; hãy sửa file .bak rồi đổi tên lại")`
   (d) Missing "nodes" or empty "nodes" -> `MapDataError("Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.")`
   (e) Missing RESTAURANT_NODE_ID -> `MapDataError(f"Bản đồ thiếu đỉnh xuất phát của quán ({RESTAURANT_NODE_ID}).")`
   (f) Graph.from_dict raises ValueError -> catch ValueError and raise `MapDataError(f"Lỗi cấu trúc đồ thị bản đồ: {err}") from err`
3. `is_valid_delivery_node(graph: Graph, node_id: str) -> bool`:
   Returns True iff node is in graph, node_id != RESTAURANT_NODE_ID, and there is a valid path from RESTAURANT to node_id (e.g. using `dijkstra(graph, RESTAURANT_NODE_ID, node_id).found`). Returns False otherwise.
4. NamedTuples:
   `SingleRoute(delivery_node_id: str, path: list[str], coords: list[tuple[float, float]], cost: float, expanded: int)`
   `RouteLeg(start: str, end: str, path: list[str], cost: float)`
   `BatchRoute(visit_order: list[str], legs: list[RouteLeg], full_path: list[str], coords: list[tuple[float, float]], total_cost: float, expanded_total: int, algorithm: str)`
5. `route_single_order(graph: Graph, delivery_node_id: str, algorithm: str = "dijkstra") -> SingleRoute`:
   Raises `ValueError` if node is not valid or unreachable. Uses `dijkstra` or `a_star` from `src.core.routing_algo`.
6. `plan_batch_route(graph: Graph, delivery_node_ids: list[str], algorithm: str = "dijkstra") -> BatchRoute`:
   - Deduplicate `delivery_node_ids` while preserving original order.
   - If empty or any node is invalid per `is_valid_delivery_node`, raise `ValueError`.
   - Nearest-Neighbor greedy routing starting at `RESTAURANT_NODE_ID`. At each step, test all unvisited candidate nodes using `dijkstra` or `a_star`. Select node with minimal cost; if tied, select candidate with lexicographically smaller ID.
   - Build legs. Accumulate `expanded_total += best.expanded` for selected legs only.
   - Concatenate `full_path`: leg 0 path + [leg.path[1:] for subsequent legs] (never duplicate consecutive juncture nodes).
   - Compute `coords` via `path_to_coordinates(full_path, graph)`.
   - Total cost = sum of leg costs.
   - Include complexity docstring: `O(k^2 (V+E) log V)`.
7. `compare_trip_algorithms(graph: Graph, delivery_node_ids: list[str]) -> dict[str, BatchRoute]`:
   Returns `{"dijkstra": plan_batch_route(..., "dijkstra"), "astar": plan_batch_route(..., "astar")}`.
8. `build_map_figure_data(graph: Graph, full_path: list[str] | None = None) -> dict[str, Any]`:
   Returns `{"nodes": [...], "edges": [...], "route": [...]}` where:
   - "nodes": list of dicts with `id, name, x, y, on_route` (on_route = bool(full_path and node_id in full_path)).
   - "edges": list of dicts with `x, y, x2, y2` for each undirected edge once (e.g. `u < v`).
   - "route": list of dicts with `step, node_id, x, y` where step is 0, 1, 2... along `full_path`.
9. Preserve `path_to_coordinates` and `get_map_render_data` with built-in typing.

VERIFICATION:
Create a temporary standalone test or run python one-liners to verify:
- Standard 3 delivery batch `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]` produces visit order `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`, full_path `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`, total cost 16.0, Dijkstra and A* both 16.0.
- All 20 existing baseline tests still pass: `uv run python -m unittest discover -s tests -t .`.
- 0 diff lines on 7 core files.

Write your handoff report to `D:\Module 1\.agents\teamwork\m1_worker\handoff.md`. Send a message when complete.
