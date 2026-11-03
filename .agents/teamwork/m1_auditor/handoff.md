# Forensic Audit Report & Handoff — Milestone M1

## Forensic Audit Summary

**Work Product**: `src/core/routing_service.py`  
**Profile**: General Project (Integrity Mode: `demo`)  
**Verdict**: **CLEAN**

### Phase Results
- **Check 1 (7 Core Files Diff)**: PASS — `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py` returned empty output (0 diff lines).
- **Check 2 (Banned Imports Scan)**: PASS — `git grep -nE "(import|from) +(heapq|bisect|queue|networkx|collections)" src` and `git grep -nE "(import|from) .*\bdeque\b" src` returned 0 import lines across all files in `src/`.
- **Check 3 (Dependency & Lockfile Integrity)**: PASS — `git diff --stat pyproject.toml uv.lock` returned empty output (0 diff lines).
- **Check 4 (Authentic Implementation & Anti-Hardcoding)**: PASS — `src/core/routing_service.py` genuinely imports and delegates to `dijkstra` and `a_star` from `src.core.routing_algo`. Nearest-neighbor heuristic, tie-breaking (`(res.cost, cand) < (best_cost, best_cand)`), duplicate handling, and leg stitching without redundant vertices are dynamically implemented. Synthetic graph test confirmed dynamic behavior with no hardcoded responses (`16.0`, customer IDs, or predetermined paths).
- **Check 5 (Baseline Test Suite)**: PASS — `uv run python -m unittest discover -s tests -t .` ran 20 tests in 0.068s with 100% OK.
- **Check 6 (MapDataError 6 Failure Modes)**: PASS — All 6 error conditions ((a) missing file, (b) empty file, (c) corrupt JSON with `.bak` file, (d) missing/empty `nodes`, (e) missing `RESTAURANT`, (f) `Graph.from_dict` ValueError) properly raise `MapDataError` with exact Vietnamese error messages.
- **Check 7 (Line Length & Formatting)**: PASS — Max line length in `src/core/routing_service.py` is 93 characters (<= 100).

---

## 1. Observation

1. **7 Core Files Diff**:
   - Command:
     ```powershell
     Set-Location "D:\Module 1"; git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
     ```
   - Result: Exit code 0, 0 lines output (empty).
   - Porcelain check:
     ```powershell
     Set-Location "D:\Module 1"; git status --porcelain -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
     ```
     Result: Exit code 0, 0 lines output.

2. **Banned Imports Scan**:
   - Command:
     ```powershell
     Set-Location "D:\Module 1"; git grep -nE "(import|from) +(heapq|bisect|queue|networkx|collections)" src
     ```
     Result: Exit code 1 (no matching lines).
   - Command:
     ```powershell
     Set-Location "D:\Module 1"; git grep -nE "(import|from) .*\bdeque\b" src
     ```
     Result: Exit code 1 (no matching lines).

3. **Packaging / Lockfile Untouched**:
   - Command:
     ```powershell
     Set-Location "D:\Module 1"; git diff --stat pyproject.toml uv.lock
     ```
     Result: Exit code 0, 0 lines output (empty).

4. **Source Code Inspection of `src/core/routing_service.py`**:
   - Lines 19-21:
     ```python
     from src.core.routing_algo import a_star, dijkstra, find_shortest_path
     from src.core.storage import _resolve_path, load_json
     from src.models.graph_node import Graph
     ```
   - `route_single_order` (Lines 177-183):
     ```python
     algo = algorithm.lower().strip()
     if algo == "dijkstra":
         result = dijkstra(graph, RESTAURANT_NODE_ID, delivery_node_id)
     elif algo in ("astar", "a_star"):
         result = a_star(graph, RESTAURANT_NODE_ID, delivery_node_id)
     ```
   - `plan_batch_route` (Lines 224-230, 261-272):
     ```python
     algo = algorithm.lower().strip()
     if algo == "dijkstra":
         search_fn = dijkstra
     elif algo in ("astar", "a_star"):
         search_fn = a_star
     ...
     for cand in unvisited:
         res = search_fn(graph, current_node, cand)
         if not res.found:
             raise ValueError(f"Không tìm thấy đường từ {current_node!r} tới {cand!r}")
         if best_cand is None or (res.cost, cand) < (best_cost, best_cand):
             best_cand = cand
             best_cost = res.cost
             best_res = res
     ```
   - Concatenation without duplicate vertices (Lines 288-294):
     ```python
     full_path: list[str] = []
     for i, leg in enumerate(legs):
         if i == 0:
             full_path.extend(leg.path)
         else:
             full_path.extend(leg.path[1:])
     ```
   - Absence of hardcoding: Ripgrep for `16`, `16.0`, or customer node literals yielded 0 matches in `src/core/routing_service.py`.

5. **Baseline Test Suite Execution**:
   - Command:
     ```powershell
     Set-Location "D:\Module 1"; uv run python -m unittest discover -s tests -t .
     ```
   - Verbatim output:
     ```
     ....................
     ----------------------------------------------------------------------
     Ran 20 tests in 0.068s

     OK
     ```

6. **Behavioral Empirical Tests**:
   - Map loading 6 error cases evaluated via `tempfile.TemporaryDirectory`:
     - Missing file -> `MapDataError: File bản đồ không tồn tại: ...`
     - Empty file -> `MapDataError: File bản đồ rỗng: ...`
     - Corrupt JSON with `.bak` -> `MapDataError: corrupt.json bị sai cú pháp và đã được đổi tên thành corrupt.json.bak; hãy sửa file .bak rồi đổi tên lại`
     - Missing `nodes` -> `MapDataError: Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.`
     - Missing `RESTAURANT` -> `MapDataError: Bản đồ thiếu đỉnh xuất phát của quán (RESTAURANT).`
     - Graph structure error -> `MapDataError: Lỗi cấu trúc đồ thị bản đồ: ...`
   - Node validation:
     - `is_valid_delivery_node` returns `False` for `"RESTAURANT"`, `""`, `None`, `123`, `"ZZZ"`, and isolated vertices.
     - Returns `True` for reachable nodes (`"CUSTOMER"`, `"CUSTOMER_2"`, `"CUSTOMER_3"`).
   - Synthetic graph test:
     - A synthetic graph with `RESTAURANT`, `NODE_Z` (weight 5.0), `NODE_A` (weight 5.0), and edge `NODE_A` - `NODE_Z` (weight 2.0) was evaluated.
     - `plan_batch_route(synth, ['NODE_Z', 'NODE_A'])` produced `visit_order = ['NODE_A', 'NODE_Z']`, `full_path = ['RESTAURANT', 'NODE_A', 'NODE_Z']`, and `total_cost = 7.0`, verifying genuine dynamic nearest-neighbor execution with correct alphabetical tie-breaking.
   - Standard 3-delivery batch on standard map:
     - Output: `visit_order = ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']`
     - `full_path = ['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`
     - `total_cost = 16.0` (both Dijkstra and A* produced identical cost and order).

7. **Line Length Check**:
   - Max line length in `src/core/routing_service.py`: 93 characters.

---

## 2. Logic Chain

1. From Observation 1, the 7 core files (`src/core/routing_algo.py`, `src/core/priority_engine.py`, `src/models/graph_node.py`, `src/models/base.py`, `src/core/storage.py`, `src/core/structures.py`, `src/core/menu_manager.py`) have exactly 0 diff, satisfying the absolute non-modification rule.
2. From Observation 2, no banned libraries (`collections`, `deque`, `heapq`, `bisect`, `queue`, `networkx`) are imported anywhere in `src/`, satisfying the dependency constraints.
3. From Observation 3, `pyproject.toml` and `uv.lock` are untouched, ensuring environment reproducibility.
4. From Observation 4 and 6, `routing_service.py` contains genuine algorithmic logic calling `dijkstra` and `a_star` without shortcutting or hardcoding results. The synthetic graph stress-test proved that tie-breaking and nearest-neighbor route chaining behave correctly and dynamically under arbitrary inputs.
5. From Observation 5 and 6, baseline tests pass completely, and all 6 error branches of `load_map_graph` strictly adhere to the specification.
6. Therefore, the implementation in `src/core/routing_service.py` is authentic, robust, compliant, and free of integrity violations.

---

## 3. Caveats

- No caveats. Every requirement in Milestone M1 was empirically verified against ground truth.

---

## 4. Conclusion

- **Verdict: CLEAN**
- Milestone M1 (`src/core/routing_service.py`) passes all forensic audit checks with zero defects or violations. Downstream milestones (M2: Order & Customer Management, M3: UI, M4: Tests) may proceed safely.

---

## 5. Verification Method

To independently reproduce and verify this audit:

1. **Verify 0 diff on 7 core files and dependencies**:
   ```powershell
   Set-Location "D:\Module 1"
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   git diff --stat pyproject.toml uv.lock
   ```
   *Expected output*: Empty.

2. **Verify absence of banned imports in src/**:
   ```powershell
   Set-Location "D:\Module 1"
   git grep -nE "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   git grep -nE "(import|from) .*\bdeque\b" src
   ```
   *Expected output*: Exit code 1 (no matches).

3. **Run baseline unit tests**:
   ```powershell
   Set-Location "D:\Module 1"
   uv run python -m unittest discover -s tests -t .
   ```
   *Expected output*: `Ran 20 tests ... OK`.

4. **Run batch route validation one-liner**:
   ```powershell
   Set-Location "D:\Module 1"
   uv run python -c "from src.core.routing_service import load_map_graph, plan_batch_route; g = load_map_graph(); b = plan_batch_route(g, ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']); assert b.visit_order == ['CUSTOMER_3', 'CUSTOMER', 'CUSTOMER_2']; assert b.full_path == ['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']; assert b.total_cost == 16.0; print('AUDIT_VERIFIED')"
   ```
   *Expected output*: `AUDIT_VERIFIED`.
