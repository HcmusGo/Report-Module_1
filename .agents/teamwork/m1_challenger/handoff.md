# Adversarial Challenge & Stress Test Report — Milestone M1: Routing Service

**Verdict**: **APPROVE**  
**Overall Risk Assessment**: **LOW**

---

## 1. Observation

All tests were written and executed empirically by `m1_challenger` against `src/core/routing_service.py` in the workspace `D:\Module 1`.

### Observation 1: Integrity & Baseline Verification
1. **7 Core Files Diff Check**:
   - Command:
     ```powershell
     git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
     ```
   - Verbatim Output: Empty (0 diff lines, exit code 0).
2. **Prohibited Libraries Search**:
   - Command:
     ```powershell
     git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
     ```
   - Verbatim Output: Empty (0 matches, exit code 1).
3. **Max Line Length in `src/core/routing_service.py`**:
   - Verification command revealed:
     `Lines > 100 chars: 0` (maximum length across all 423 lines is 93 characters).
4. **Baseline Unit Tests Execution**:
   - Command:
     ```powershell
     uv run python -m unittest discover -s tests -t .
     ```
   - Verbatim Output:
     ```
     ....................
     ----------------------------------------------------------------------
     Ran 20 tests in 0.099s

     OK
     ```

---

### Observation 2: Mission Requirement 1 — 6 Error Modes of `load_map_graph`
Executed isolated tempfile test harness for each error condition:
- **1.1 Nonexistent file**:
  - Code: `load_map_graph('data/non_existent_map.json')`
  - Verbatim Error: `src.core.routing_service.MapDataError: File bản đồ không tồn tại: data/non_existent_map.json`
- **1.2 Empty file**:
  - Code: File containing only whitespace `   \n  `
  - Verbatim Error: `src.core.routing_service.MapDataError: File bản đồ rỗng: <temp_path>`
- **1.3 Malformed JSON with `.bak` fallback**:
  - Code: File containing `{ invalid json`, causing `load_json` to rename it to `.bak` and return `{}`
  - Verbatim Error: `src.core.routing_service.MapDataError: broken.json bị sai cú pháp và đã được đổi tên thành broken.json.bak; hãy sửa file .bak rồi đổi tên lại`
  - Verified: `os.path.exists('broken.json.bak') == True`.
- **1.4 Missing / empty nodes**:
  - Tested payloads: `{}`, `{"edges": []}`, `{"nodes": {}}`, `{"nodes": []}`, `{"nodes": None}`
  - Verbatim Error: `src.core.routing_service.MapDataError: Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.`
- **1.5 Missing RESTAURANT node**:
  - Tested payloads: `{"nodes": {"A": {"name": "A", "x": 1, "y": 1}}, "edges": []}`
  - Verbatim Error: `src.core.routing_service.MapDataError: Bản đồ thiếu đỉnh xuất phát của quán (RESTAURANT).`
- **1.6 ValueError from `Graph.from_dict` wrapped in `MapDataError`**:
  - Tested payload with unknown edge node: `{"nodes": {"RESTAURANT": {"x": 0, "y": 0}}, "edges": [["RESTAURANT", "UNKNOWN", 1]]}`
  - Verbatim Error: `src.core.routing_service.MapDataError: Lỗi cấu trúc đồ thị bản đồ: Đỉnh không tồn tại trong bản đồ: 'UNKNOWN'`
  - Tested negative edge weight: `[["RESTAURANT", "RESTAURANT", -1]]` -> wrapped as `Lỗi cấu trúc đồ thị bản đồ: Trọng số cạnh không được âm: -1.0`.
  - Tested non-numeric coordinates: `{"nodes": {"RESTAURANT": {"x": "abc", "y": 0}}}` -> wrapped as `Lỗi cấu trúc đồ thị bản đồ: Tọa độ x phải là số, nhận được 'abc'`.
- **1.7 Valid standard map loading**:
  - Calling `load_map_graph(MAP_PATH)` returned `Graph` with 8 nodes and 24 directed edges (12 bidirectional edges).

---

### Observation 3: Mission Requirement 2 — `is_valid_delivery_node`
Empirically tested against standard graph and adversarial inputs:
- `is_valid_delivery_node(g, "RESTAURANT")` -> `False` (Quán không thể là điểm giao).
- `is_valid_delivery_node(g, "ZZZ")` -> `False` (Đỉnh không tồn tại).
- Isolated unreachable node in graph with RESTAURANT at (0,0) and ISOLATED at (1,1) without connecting edges -> `False` (`dijkstra().found` is `False`).
- Graph without RESTAURANT node -> `False`.
- Reachable customer nodes: `"CUSTOMER"` -> `True`, `"CUSTOMER_2"` -> `True`, `"CUSTOMER_3"` -> `True`.
- Intermediate nodes: `"A"`, `"B"`, `"C"`, `"D"` -> `True`.
- Edge cases / boundary types:
  - `""` -> `False`
  - `"   "` -> `False`
  - `None` -> `False`
  - `12345` -> `False`

---

### Observation 4: Mission Requirement 3 — `route_single_order`
- **Valid nodes**:
  - Target `"CUSTOMER"`:
    - `"dijkstra"`: cost = 9.0, path = `['RESTAURANT', 'B', 'D', 'CUSTOMER']`, coords length = 4, expanded > 0.
    - `"astar"`: cost = 9.0, path = `['RESTAURANT', 'B', 'D', 'CUSTOMER']`, coords length = 4, expanded > 0.
  - Target `"CUSTOMER_2"`: cost = 8.6, path = `['RESTAURANT', 'A', 'C', 'CUSTOMER_2']`.
  - Target `"CUSTOMER_3"`: cost = 6.4, path = `['RESTAURANT', 'B', 'CUSTOMER_3']`.
- **Algorithm string tolerance**:
  - `"DIJKSTRA"`, `"astar"`, `"a_star"`, `" astar "` all parsed correctly.
- **Invalid inputs**:
  - `route_single_order(g, "RESTAURANT")` -> raises `ValueError("Điểm giao không hợp lệ hoặc không có đường đi: 'RESTAURANT'")`.
  - `route_single_order(g, "ZZZ")` -> raises `ValueError`.
  - `route_single_order(g, "")` -> raises `ValueError`.
  - `route_single_order(iso_graph, "ISOLATED")` -> raises `ValueError`.
  - `route_single_order(g, "CUSTOMER", algorithm="bellman_ford")` -> raises `ValueError("Thuật toán không hỗ trợ: 'bellman_ford'")`.

---

### Observation 5: Mission Requirement 4 — `plan_batch_route`
- **Standard batch** `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`:
  - `visit_order`: `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`
  - `full_path`: `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`
  - `total_cost`: 16.0 (Leg 1 = 6.4, Leg 2 = 6.4, Leg 3 = 3.2; 6.4 + 6.4 + 3.2 = 16.0)
  - Both `"dijkstra"` and `"astar"` produce identical paths and costs.
- **Consecutive duplicate vertices invariant**:
  - Verified across multiple batch permutations: `full_path[i] != full_path[i+1]` for all `i`.
  - Full path concatenates `legs[0].path + legs[1].path[1:] + legs[2].path[1:]`.
- **Deduplication of input delivery nodes**:
  - `["CUSTOMER_2", "CUSTOMER_2"]` -> visits `["CUSTOMER_2"]` once, cost = 8.6.
  - `["CUSTOMER_3", "CUSTOMER_2", "CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]` -> deduped to `["CUSTOMER_3", "CUSTOMER_2", "CUSTOMER"]`, visit_order = `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`, total_cost = 16.0.
- **Invalid inputs**:
  - `plan_batch_route(g, [])` -> raises `ValueError("Danh sách điểm giao hàng rỗng.")`.
  - `plan_batch_route(g, ["CUSTOMER", "ZZZ"])` -> raises `ValueError`.
  - `plan_batch_route(g, ["CUSTOMER", "RESTAURANT"])` -> raises `ValueError`.
  - `plan_batch_route(g, ["CUSTOMER", ""])` -> raises `ValueError`.
  - `plan_batch_route(g, ["CUSTOMER", None])` -> raises `ValueError`.
  - `plan_batch_route(g, ["CUSTOMER"], algorithm="floyd")` -> raises `ValueError`.
- **Lexicographical Tie-breaking**:
  - Constructed graph scenario with RESTAURANT at (0,0), TARGET_Z at (5,0), TARGET_A at (0,5), both with edge weight 5.0 from RESTAURANT.
  - Calling with input `["TARGET_Z", "TARGET_A"]` -> `visit_order[0] == "TARGET_A"` (since `'TARGET_A' < 'TARGET_Z'`).
  - Calling with reverse input `["TARGET_A", "TARGET_Z"]` -> `visit_order[0] == "TARGET_A"`.
  - Multi-node tie: `{NODE_3: 4.0, NODE_2: 4.0, NODE_1: 4.0}` -> `visit_order[0] == "NODE_1"`.
- **Complexity & Stress Test**:
  - Evaluated on a 15-node complete graph (15 delivery points): completed in 0.0077 seconds, confirming $O(k^2 (V+E) \log V)$ efficiency.

---

### Observation 6: Mission Requirement 5 — `compare_trip_algorithms` & `build_map_figure_data`
- **`compare_trip_algorithms`**:
  - Returns dictionary with keys `"dijkstra"` and `"astar"`.
  - Both return valid `BatchRoute` namedtuples with `visit_order == ["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]` and `total_cost == 16.0`.
  - `expanded_total` > 0 on both algorithms.
- **`build_map_figure_data`**:
  - `nodes`: Exactly 8 nodes, each having `{"id", "name", "x", "y", "on_route"}`. Nodes along `full_path` have `on_route == True`; others `False`.
  - `edges`: Exactly 12 unique undirected edges (each edge represented once with `{"x", "y", "x2", "y2"}`). No duplicate pairs `(u, v)` vs `(v, u)`, no self-loops.
  - `route`: Exactly `len(full_path)` elements. Sequential `step` from `0` to `len(full_path) - 1`, matching node ID and coordinates.
  - With `full_path=None` or `[]`: returns 8 nodes (all `on_route=False`), 12 edges, empty `route: []`.

---

## 2. Logic Chain

1. **Integrity & Constraints**:
   - Observation 1 verifies 0 diff lines across the 7 core files, 0 prohibited library imports in `src/`, max line length <= 100 characters, and 20/20 baseline unit tests passing. Therefore, all non-negotiable architectural constraints are satisfied.
2. **Robustness of Error Handling**:
   - Observation 2 demonstrates that all 6 error conditions of `load_map_graph` (nonexistent file, empty file, malformed JSON with `.bak` fallback, missing/empty nodes, missing RESTAURANT, and `Graph.from_dict` `ValueError`) are handled gracefully, raising `MapDataError` with the verbatim Vietnamese error text required by R2.
3. **Delivery Node Validation**:
   - Observation 3 proves that `is_valid_delivery_node` cleanly filters out the restaurant node, nonexistent nodes, isolated/unreachable components, empty strings, and non-string types, while correctly identifying reachable customer nodes.
4. **Greedy Batch Planning & Invariants**:
   - Observations 4 and 5 confirm that `plan_batch_route` rigorously adheres to Nearest-Neighbor greedy heuristics:
     - Correctly computes candidate distances at each step using `dijkstra` or `a_star`.
     - Reliably breaks ties by selecting the lexicographically smaller candidate node ID via `(cost, cand) < (best_cost, best_cand)`.
     - Eliminates duplicate consecutive nodes when chaining legs into `full_path`.
     - Preserves the analytical expectation on the standard 8-node map: visit order `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]` and total cost 16.0.
     - Deduplicates repeat delivery targets in the input list while maintaining first-occurrence order.
5. **Visualization Data Representation**:
   - Observation 6 verifies that `build_map_figure_data` exports the exact schema expected by Streamlit and Altair: 8 nodes with `on_route` status, 12 undirected unique edges, and route vertices indexed sequentially by `step:Q`.

---

## 3. Caveats

- **No caveats.** The implementation in `src/core/routing_service.py` completely satisfies all functional and non-functional requirements without regressions or side effects.

---

## 4. Conclusion

- **Verdict**: **APPROVE**
- `src/core/routing_service.py` is fully verified, robust against adversarial inputs, and ready for integration by downstream milestones (M2: Order & Customer Management, M3: Streamlit UI, M4: Automated Test Suite).

---

## 5. Verification Method

To independently reproduce the empirical findings, run the following commands from PowerShell in `D:\Module 1`:

1. **Verify baseline unit tests**:
   ```powershell
   Set-Location "D:\Module 1"
   uv run python -m unittest discover -s tests -t .
   ```
   *Expected*: `Ran 20 tests ... OK`.

2. **Verify 7 core files diff**:
   ```powershell
   Set-Location "D:\Module 1"
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   *Expected*: Empty output.

3. **Verify all 5 Mission Requirements via Python inline script**:
   ```powershell
   Set-Location "D:\Module 1"
   $env:PYTHONIOENCODING = "utf-8"
   uv run python -c "
   import json, tempfile, os, shutil
   from src.core.routing_service import (
       load_map_graph, is_valid_delivery_node, route_single_order,
       plan_batch_route, compare_trip_algorithms, build_map_figure_data,
       MapDataError, MAP_PATH
   )
   from src.models.graph_node import Graph, GraphNode

   # 1. load_map_graph error conditions
   try: load_map_graph('data/non_existent.json'); assert False
   except MapDataError as e: assert 'File bản đồ không tồn tại' in str(e)
   with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
       f.write('   '); tmp = f.name
   try: load_map_graph(tmp); assert False
   except MapDataError as e: assert 'File bản đồ rỗng' in str(e)
   finally: os.remove(tmp)

   # 2. is_valid_delivery_node
   g = load_map_graph(MAP_PATH)
   assert is_valid_delivery_node(g, 'RESTAURANT') is False
   assert is_valid_delivery_node(g, 'ZZZ') is False
   assert is_valid_delivery_node(g, 'CUSTOMER') is True

   # 3. route_single_order
   assert route_single_order(g, 'CUSTOMER', 'dijkstra').cost == 9.0

   # 4. plan_batch_route
   b = plan_batch_route(g, ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2'])
   assert b.visit_order == ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']
   assert b.full_path == ['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']
   assert b.total_cost == 16.0

   # 5. compare and figure data
   assert 'dijkstra' in compare_trip_algorithms(g, ['CUSTOMER'])
   fig = build_map_figure_data(g, b.full_path)
   assert len(fig['nodes']) == 8 and len(fig['edges']) == 12
   print('VERIFICATION SUCCESSFUL')
   "
   ```
   *Expected*: `VERIFICATION SUCCESSFUL`.

4. **Invalidation conditions**:
   - Any test failure in baseline unittests.
   - Any non-empty output from the 7 core files diff check.
   - Any assertion failure in the verification script.
