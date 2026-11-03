# Review & Adversarial Challenge Report: Milestone M0 (Baseline & Data Setup)

## Review Summary
**Verdict**: **APPROVE**

Milestone M0 has been thoroughly inspected, tested, and adversarial-stress-tested. All 7 dispatch requirements are strictly met, 0 core files were touched, 0 prohibited libraries were detected, and baseline tests pass 100%.

---

## 1. Observation

### Obs 1: Git Branch Verification
- Command: `Set-Location "D:\Module 1"; git branch --show-current`
- Verbatim Output:
  ```
  feat/connect-routing-order
  ```

### Obs 2: Standard Map Graph Dataset (`data/map_graph.json`)
- File path: `D:\Module 1\data\map_graph.json`
- Node count: exactly 8 nodes:
  - `RESTAURANT`: `{"name": "Quán ăn", "x": 0.0, "y": 0.0}`
  - `A`: `{"name": "Ngã tư A", "x": 2.0, "y": 2.0}`
  - `B`: `{"name": "Ngã tư B", "x": 3.0, "y": -1.0}`
  - `C`: `{"name": "Ngã ba C", "x": 5.0, "y": 2.0}`
  - `D`: `{"name": "Ngã tư D", "x": 6.0, "y": -1.0}`
  - `CUSTOMER`: `{"name": "Nhà khách hàng", "x": 8.0, "y": 1.0}`
  - `CUSTOMER_2`: `{"name": "Nhà khách hàng 2", "x": 7.0, "y": 4.0}`
  - `CUSTOMER_3`: `{"name": "Nhà khách hàng 3", "x": 4.0, "y": -4.0}`
- Edge count: exactly 12 bidirectional edges (yielding 24 directed edges in `Graph`):
  `["RESTAURANT", "A", 2.8]`, `["RESTAURANT", "B", 3.2]`, `["A", "B", 3.2]`, `["A", "C", 3.0]`, `["B", "D", 3.0]`, `["C", "D", 3.2]`, `["C", "CUSTOMER", 3.2]`, `["D", "CUSTOMER", 2.8]`, `["C", "CUSTOMER_2", 2.8]`, `["CUSTOMER", "CUSTOMER_2", 3.2]`, `["B", "CUSTOMER_3", 3.2]`, `["D", "CUSTOMER_3", 3.6]`.
- Routing verification script executed against `data/map_graph.json`:
  ```python
  Node IDs: ['RESTAURANT', 'A', 'B', 'C', 'D', 'CUSTOMER', 'CUSTOMER_2', 'CUSTOMER_3']
  Node count: 8
  Directed edge count: 24
  RESTAURANT -> CUSTOMER_3 (Dijkstra): ['RESTAURANT', 'B', 'CUSTOMER_3'] 6.4 expanded: 6
  CUSTOMER_3 -> CUSTOMER (Dijkstra): ['CUSTOMER_3', 'D', 'CUSTOMER'] 6.4 expanded: 5
  CUSTOMER -> CUSTOMER_2 (Dijkstra): ['CUSTOMER', 'CUSTOMER_2'] 3.2 expanded: 4
  Total cost Dijkstra: 16.0
  Full path: ['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']
  A* costs: 6.4 6.4 3.2 total: 16.0
  ```

### Obs 3: Standard User Dataset (`data/users.json`)
- File path: `D:\Module 1\data\users.json`
- Content: Exactly 4 customer records:
  - `U001`: name "Nguyễn Văn An", email "an@example.com", is_vip: true, node_id: "CUSTOMER"
  - `U002`: name "Trần Thị Bình", email "binh@example.com", is_vip: false, node_id: "CUSTOMER_2"
  - `U003`: name "Lê Văn Cường", email "cuong@example.com", is_vip: false, node_id: "CUSTOMER_3"
  - `U004`: name "Phạm Thu Dung", email "dung@example.com", is_vip: true, node_id: "CUSTOMER_2"

### Obs 4: Import Cleanup in `src/models/menu_item.py`
- File path: `D:\Module 1\src\models\menu_item.py` lines 10-17:
  ```python
  from __future__ import annotations

  from typing import Any

  from src.models.base import BaseEntity


  class MenuItem(BaseEntity):
  ```
- Git diff confirms replacement of the `try ... from models.base ... except ...` block with direct `from src.models.base import BaseEntity`.

### Obs 5: Baseline Test Suite Execution
- Command: `uv run python -m unittest discover -s tests -t .`
- Verbatim Output:
  ```
  ....................
  ----------------------------------------------------------------------
  Ran 20 tests in 0.171s

  OK
  ```
- 20 unit tests executed, 0 failures, 0 errors.

### Obs 6: Protected Core Files Integrity
- Command: `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
- Verbatim Output: (empty, exit code 0; 0 diff lines).
- Comparison against `main` also yielded 0 diff lines.

### Obs 7: Prohibited Libraries AST and Regex Audit
- Python AST Walk over all files in `src/` and `tests/` checking for imports of `heapq`, `bisect`, `queue`, `networkx`, and `collections.deque`:
  - Output: `AST scan passed: 0 banned libraries in src/` and `AST scan passed: 0 banned libraries in tests/`.
- Regex scan `(import|from)\s+(heapq|bisect|queue|networkx|collections)` across all project files:
  - Output: `Matches count: 0`.

---

## 2. Logic Chain

1. *Branch Setup (Obs 1)*: The repository is properly isolated on `feat/connect-routing-order`. All subsequent changes are constrained to this feature branch as required by §R5.
2. *Graph Correctness & Benchmark Fitness (Obs 2)*: Loading `data/map_graph.json` into `Graph` confirms that the 8 nodes and 12 bidirectional edges establish a connected planar graph. Evaluating the benchmark dispatch trip `[CUSTOMER_3, CUSTOMER, CUSTOMER_2]` produces the exact visit order and full path `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']` with a total cost of 16.0 km across both Dijkstra and A*, proving that the graph data matches the exact requirements for Milestones M1-M5.
3. *Customer Integrity (Obs 3)*: All 4 users in `data/users.json` reference valid delivery nodes that exist on the map and are reachable from the restaurant. The VIP and non-VIP distributions allow testing both priority and normal order flows.
4. *Clean Code Layout (Obs 4)*: `src/models/menu_item.py` now uses the canonical package-relative import path without runtime fallback overhead, adhering to standard repository conventions.
5. *Regression Safety (Obs 5)*: The existing 20 unit tests pass without failure, confirming that updating data files and cleaning up `menu_item.py` introduced zero regressions.
6. *Architectural Integrity (Obs 6 & Obs 7)*: Zero modifications were made to the 7 core files, and zero banned libraries were imported or introduced into the project.

---

## 3. Adversarial Stress-Testing & Integrity Checks

### Integrity Violation Checks
| Pattern | Detection Status | Assessment |
|---|---|---|
| Hardcoded test passes / shortcuts | None detected | Working copy changes contain only standard data and import cleanup |
| Dummy or facade implementations | None detected | No mock or stub logic introduced |
| Bypassed core tasks | None detected | Exact requested tasks performed |
| Fabricated verification outputs | None detected | Worker execution logs matched independent re-runs |
| Test suite tampering | None detected | `git diff tests/` is clean (0 modifications) |

### Attack Scenarios Tested
- **Scenario 1: A\* Heuristic Admissibility on New Map**
  - *Attack*: Check if any edge distance in the new graph violates $h(u) \le w(u, v) + h(v)$ or makes Euclidean distance inadmissible.
  - *Result*: `g.heuristic_scale()` computed to `0.989949`, satisfying $k \cdot \text{Euclid}(u, v) \le w$ for all 24 directed edges. A* is mathematically guaranteed optimal and admissible.
- **Scenario 2: Graph Connectivity and Dead-End Nodes**
  - *Attack*: Check if any of the customer nodes (`CUSTOMER`, `CUSTOMER_2`, `CUSTOMER_3`) are isolated or lack a return/forward path.
  - *Result*: All nodes are reachable from `RESTAURANT`, and each node has at least 2 neighbors.
- **Scenario 3: Non-ASCII & Encoding Integrity**
  - *Attack*: Check if JSON files can be safely read and parsed with standard `utf-8` decoders.
  - *Result*: `json.load(open(..., encoding='utf-8'))` parsed all Vietnamese diacritics without syntax or Unicode errors.

---

## 4. Caveats
- No caveats. Data files match exact coordinates, names, and weights specified in the dispatch. All 7 protected files remain untouched.

---

## 5. Conclusion
**Verdict**: **APPROVE**
- Milestone M0 satisfies all acceptance criteria with complete architectural and algorithmic fidelity.
- Proceed to Milestone M1 (`routing_service.py`).

---

## 6. Verification Method

To independently reproduce this verification:

1. **Verify git branch**:
   ```powershell
   Set-Location "D:\Module 1"; git branch --show-current
   ```
   *Expected output*: `feat/connect-routing-order`

2. **Verify 20 unit tests**:
   ```powershell
   Set-Location "D:\Module 1"; uv run python -m unittest discover -s tests -t .
   ```
   *Expected output*: `Ran 20 tests in ... OK`

3. **Verify 0 diff on 7 core files**:
   ```powershell
   Set-Location "D:\Module 1"; git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   *Expected output*: Empty output (0 diff lines).

4. **Verify graph topology and 16.0 km benchmark**:
   ```powershell
   Set-Location "D:\Module 1"; uv run python -c "import json; from src.models.graph_node import Graph; from src.core.routing_algo import dijkstra; g = Graph.from_dict(json.load(open('data/map_graph.json', encoding='utf-8'))); assert len(g.node_ids) == 8; p1, c1, _ = dijkstra(g, 'RESTAURANT', 'CUSTOMER_3'); p2, c2, _ = dijkstra(g, 'CUSTOMER_3', 'CUSTOMER'); p3, c3, _ = dijkstra(g, 'CUSTOMER', 'CUSTOMER_2'); assert (c1 + c2 + c3) == 16.0; print('Graph verification PASSED')"
   ```
   *Expected output*: `Graph verification PASSED`

5. **Verify zero banned library imports**:
   ```powershell
   Set-Location "D:\Module 1"; uv run python -c "import ast, os, sys; banned = {'heapq', 'bisect', 'queue', 'networkx'}; [sys.exit(1) for r, _, fs in os.walk('src') for f in fs if f.endswith('.py') for n in ast.walk(ast.parse(open(os.path.join(r, f), encoding='utf-8').read())) if (isinstance(n, ast.Import) and any(a.name in banned for a in n.names)) or (isinstance(n, ast.ImportFrom) and n.module in banned)]; print('Zero banned imports PASSED')"
   ```
   *Expected output*: `Zero banned imports PASSED`
