# Handoff Report — Milestone M1: Routing Service

## 1. Observation
- Target file `src/core/routing_service.py` was implemented to fulfill all Milestone M1 specifications.
- Baseline test execution command:
  `uv run python -m unittest discover -s tests -t .`
  Result:
  ```
  ....................
  ----------------------------------------------------------------------
  Ran 20 tests in 0.077s

  OK
  ```
- 7 core files diff check command:
  `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
  Result: 0 diff lines (empty output).
- Max line length in `src/core/routing_service.py`: 93 characters (<= 100).
- Prohibited imports check (`collections`, `deque`, `heapq`, `bisect`, `queue`, `networkx`): 0 imports found in `src/core/routing_service.py`.
- Comprehensive standalone verification executed covering:
  - `load_map_graph()` 6 failure modes with verbatim Vietnamese messages:
    (a) File does not exist: `File bản đồ không tồn tại: {path}`
    (b) File empty: `File bản đồ rỗng: {path}`
    (c) JSON syntax error: `{Path(path).name} bị sai cú pháp và đã được đổi tên thành {Path(path).name}.bak; hãy sửa file .bak rồi đổi tên lại`
    (d) Missing/empty nodes: `Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.`
    (e) Missing restaurant: `Bản đồ thiếu đỉnh xuất phát của quán (RESTAURANT).`
    (f) Graph.from_dict ValueError: `Lỗi cấu trúc đồ thị bản đồ: {err}`
  - `is_valid_delivery_node()` returns False for "RESTAURANT", "ZZZ", empty string, and isolated nodes; returns True for reachable delivery nodes.
  - `route_single_order()` with Dijkstra and A*.
  - `plan_batch_route()` with standard 3 delivery batch `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`:
    - `visit_order`: `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`
    - `full_path`: `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`
    - `total_cost`: 16.0 (Dijkstra and A* identical)
    - Consecutive juncture deduplication confirmed.
    - Delivery list deduplication preserving first occurrence confirmed.
    - Invalid node / empty list raises `ValueError`.
  - `compare_trip_algorithms()` returns dict with `"dijkstra"` and `"astar"` BatchRoute objects.
  - `build_map_figure_data()` returns `"nodes"` (8 nodes, `on_route` flag), `"edges"` (12 undirected edges with `x, y, x2, y2`), `"route"` (steps 0, 1, 2... along `full_path`).
  - Preserved `path_to_coordinates()` and `get_map_render_data()` with builtin types.

## 2. Logic Chain
1. Based on Observation 1 and 2, all 20 existing unit tests continue to pass without regression, demonstrating that `routing_service.py` maintains full backward compatibility with `get_map_render_data` and `path_to_coordinates`.
2. Based on Observation 3 and 4, the mandatory constraints (only write `src/core/routing_service.py`, zero edits on 7 core files, zero prohibited library imports, max line length <= 100) are fully satisfied.
3. Based on Observation 5, all 6 error branches of `load_map_graph` correctly raise `MapDataError` with the required Vietnamese text and `.bak` handling.
4. Nearest-Neighbor greedy routing in `plan_batch_route` accurately evaluates candidates at each step using `dijkstra` or `a_star`, applies lexicographical tie-breaking on `cand` ID, joins paths without duplicate vertices, and calculates `expanded_total` exclusively for selected legs.
5. On the standard 8-node map with customers `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`, the computed path and total distance 16.0 match the exact analytical expectation.

## 3. Caveats
- No caveats. The implementation strictly adheres to the requested interfaces, algorithms, and constraints.

## 4. Conclusion
Milestone M1 (`src/core/routing_service.py`) is complete, fully verified, and ready for integration by downstream milestones (M2: Order & Customer Management, M3: UI, M4: Formal Test Suite).

## 5. Verification Method
1. Run baseline unit tests:
   `Set-Location 'D:\Module 1'; uv run python -m unittest discover -s tests -t .`
   Must output: `Ran 20 tests ... OK`.
2. Check 7 core files diff:
   `Set-Location 'D:\Module 1'; git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
   Must output empty string.
3. Verify standard 3-delivery batch via Python one-liner:
   `Set-Location 'D:\Module 1'; uv run python -c "from src.core.routing_service import load_map_graph, plan_batch_route; g = load_map_graph(); b = plan_batch_route(g, ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']); assert b.visit_order == ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']; assert b.full_path == ['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']; assert b.total_cost == 16.0; print('SUCCESS')"`
   Must output: `SUCCESS`.
4. Invalidation conditions: Any test failure in baseline tests, any diff on the 7 core files, or any output other than `SUCCESS` on the standard batch verification.
